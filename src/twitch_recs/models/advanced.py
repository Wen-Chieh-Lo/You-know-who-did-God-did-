from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numba import njit
from scipy import sparse


def _require_torch():
    try:
        import torch
        return torch
    except (ImportError, OSError) as exc:
        raise RuntimeError(
            "Advanced neural recommenders require a working PyTorch installation. "
            "On the project machine use scripts/run_advanced.sh, which supplies the "
            "Intel ITT compatibility library required by the installed PyTorch build."
        ) from exc


@njit(cache=True)
def _sample_unseen(indptr: np.ndarray, indices: np.ndarray, users: np.ndarray,
                   n_items: int, seed: int) -> np.ndarray:
    np.random.seed(seed)
    result = np.empty(len(users), dtype=np.int64)
    for position in range(len(users)):
        user = users[position]
        history = indices[indptr[user]:indptr[user + 1]]
        item = np.random.randint(0, n_items)
        while np.searchsorted(history, item) < len(history) and history[np.searchsorted(history, item)] == item:
            item = np.random.randint(0, n_items)
        result[position] = item
    return result


def build_sequences(fit, max_length: int = 50) -> list[np.ndarray]:
    """Return chronological item sequences aligned to fit user indices."""
    ordered = fit.frame.sort_values(["user_idx", "time_start"], kind="stable")
    sequences: list[np.ndarray] = [np.empty(0, dtype=np.int64) for _ in fit.user_names]
    for user, group in ordered.groupby("user_idx", sort=False):
        values = group["item_idx"].to_numpy(dtype=np.int64)
        sequences[int(user)] = values[-max_length:]
    return sequences


@dataclass
class EmbeddingScores:
    user_factors: np.ndarray
    item_factors: np.ndarray

    def score_user(self, user: int) -> np.ndarray:
        return self.item_factors @ self.user_factors[int(user)]


class LightGCN:
    """Memory-bounded LightGCN with sampled BPR training.

    The full normalized user-item graph is propagated every epoch.  To fit the
    100k Twitch graph on a 6 GiB GPU, each epoch optimizes a deterministic sample
    of positive edges rather than materializing every training triple at once.
    """

    def __init__(self, factors: int = 64, layers: int = 2, epochs: int = 10,
                 learning_rate: float = 0.01, regularization: float = 1e-4,
                 samples_per_epoch: int = 250_000, seed: int = 258,
                 device: str | None = None):
        self.factors = int(factors)
        self.layers = int(layers)
        self.epochs = int(epochs)
        self.learning_rate = float(learning_rate)
        self.regularization = float(regularization)
        self.samples_per_epoch = int(samples_per_epoch)
        self.seed = int(seed)
        self.device = device
        self.user_factors_: np.ndarray | None = None
        self.item_factors_: np.ndarray | None = None

    def fit(self, interactions: sparse.csr_matrix) -> "LightGCN":
        torch = _require_torch()
        x = interactions.tocsr(copy=True)
        x.sort_indices()
        n_users, n_items = x.shape
        device = torch.device(self.device or ("cuda" if torch.cuda.is_available() else "cpu"))
        users, items = x.nonzero()
        users = users.astype(np.int64)
        items = items.astype(np.int64)

        rows = np.concatenate([users, n_users + items])
        cols = np.concatenate([n_users + items, users])
        degrees = np.bincount(rows, minlength=n_users + n_items).astype(np.float32)
        weights = 1.0 / np.sqrt(degrees[rows] * degrees[cols])
        adjacency = torch.sparse_coo_tensor(
            torch.as_tensor(np.vstack([rows, cols]), dtype=torch.long, device=device),
            torch.as_tensor(weights, dtype=torch.float32, device=device),
            (n_users + n_items, n_users + n_items), device=device,
        ).coalesce()

        generator = torch.Generator(device=device)
        generator.manual_seed(self.seed)
        embeddings = torch.nn.Embedding(n_users + n_items, self.factors, device=device)
        torch.nn.init.normal_(embeddings.weight, std=0.1 / np.sqrt(max(1, self.factors)),
                              generator=generator)
        optimizer = torch.optim.Adam(embeddings.parameters(), lr=self.learning_rate)
        rng = np.random.default_rng(self.seed)

        for epoch in range(self.epochs):
            count = min(self.samples_per_epoch, len(users))
            selected = rng.choice(len(users), size=count, replace=False)
            sampled_users = users[selected]
            positive_items = items[selected]
            negative_items = _sample_unseen(
                x.indptr.astype(np.int64), x.indices.astype(np.int64), sampled_users,
                n_items, self.seed + epoch,
            )

            propagated = embeddings.weight
            layers = [propagated]
            for _ in range(self.layers):
                propagated = torch.sparse.mm(adjacency, propagated)
                layers.append(propagated)
            final = torch.stack(layers, dim=0).mean(dim=0)
            u = torch.as_tensor(sampled_users, dtype=torch.long, device=device)
            pos = torch.as_tensor(positive_items + n_users, dtype=torch.long, device=device)
            neg = torch.as_tensor(negative_items + n_users, dtype=torch.long, device=device)
            positive_scores = (final[u] * final[pos]).sum(dim=1)
            negative_scores = (final[u] * final[neg]).sum(dim=1)
            ranking_loss = torch.nn.functional.softplus(negative_scores - positive_scores).mean()
            raw = embeddings.weight
            reg_loss = (
                raw[u].pow(2).sum() + raw[pos].pow(2).sum() + raw[neg].pow(2).sum()
            ) / (2.0 * count)
            loss = ranking_loss + self.regularization * reg_loss
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            optimizer.step()

        with torch.no_grad():
            propagated = embeddings.weight
            layers = [propagated]
            for _ in range(self.layers):
                propagated = torch.sparse.mm(adjacency, propagated)
                layers.append(propagated)
            final = torch.stack(layers, dim=0).mean(dim=0).cpu().numpy().astype(np.float32)
        self.user_factors_ = final[:n_users]
        self.item_factors_ = final[n_users:]
        return self

    def score_user(self, user: int) -> np.ndarray:
        if self.user_factors_ is None or self.item_factors_ is None:
            raise RuntimeError("Call fit before scoring")
        return self.item_factors_ @ self.user_factors_[int(user)]


class SequentialRecommender:
    """Sampled-next-item GRU4Rec or SASRec model using only interaction order."""

    def __init__(self, architecture: str, factors: int = 64, max_length: int = 50,
                 epochs: int = 8, batch_size: int = 512, learning_rate: float = 1e-3,
                 seed: int = 258, device: str | None = None):
        if architecture not in {"gru4rec", "sasrec"}:
            raise ValueError("architecture must be 'gru4rec' or 'sasrec'")
        self.architecture = architecture
        self.factors = int(factors)
        self.max_length = int(max_length)
        self.epochs = int(epochs)
        self.batch_size = int(batch_size)
        self.learning_rate = float(learning_rate)
        self.seed = int(seed)
        self.device = device
        self.item_factors_: np.ndarray | None = None
        self.user_factors_: np.ndarray | None = None

    def fit(self, fit) -> "SequentialRecommender":
        torch = _require_torch()
        nn = torch.nn
        device = torch.device(self.device or ("cuda" if torch.cuda.is_available() else "cpu"))
        torch.manual_seed(self.seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(self.seed)
        sequences = build_sequences(fit, self.max_length + 1)
        eligible_users = np.asarray([u for u, seq in enumerate(sequences) if len(seq) >= 2], dtype=np.int64)
        n_items = fit.matrix.shape[1]

        class Model(nn.Module):
            def __init__(inner):
                super().__init__()
                inner.items = nn.Embedding(n_items + 1, self.factors, padding_idx=0)
                if self.architecture == "gru4rec":
                    inner.encoder = nn.GRU(self.factors, self.factors, batch_first=True)
                    inner.positions = None
                else:
                    inner.positions = nn.Embedding(self.max_length, self.factors)
                    layer = nn.TransformerEncoderLayer(
                        self.factors, nhead=2, dim_feedforward=self.factors * 2,
                        dropout=0.1, batch_first=True, norm_first=True,
                    )
                    inner.encoder = nn.TransformerEncoder(layer, num_layers=2)

            def encode(inner, values, lengths):
                embedded = inner.items(values)
                if self.architecture == "gru4rec":
                    packed = nn.utils.rnn.pack_padded_sequence(
                        embedded, lengths.cpu(), batch_first=True, enforce_sorted=False
                    )
                    _, hidden = inner.encoder(packed)
                    return hidden[-1]
                positions = torch.arange(values.shape[1], device=values.device)
                embedded = embedded + inner.positions(positions)[None, :, :]
                causal = torch.triu(torch.ones(values.shape[1], values.shape[1],
                                                device=values.device, dtype=torch.bool), diagonal=1)
                padding = values.eq(0)
                encoded = inner.encoder(embedded, mask=causal, src_key_padding_mask=padding)
                return encoded[torch.arange(len(lengths), device=values.device), lengths - 1]

        model = Model().to(device)
        optimizer = torch.optim.Adam(model.parameters(), lr=self.learning_rate)
        rng = np.random.default_rng(self.seed)

        def make_batch(batch_users: np.ndarray, epoch: int):
            prefixes, positives = [], []
            for user in batch_users:
                seq = sequences[int(user)]
                end = int(rng.integers(1, len(seq)))
                prefix = seq[max(0, end - self.max_length):end]
                prefixes.append(prefix)
                positives.append(int(seq[end]))
            width = max(map(len, prefixes))
            values = np.zeros((len(prefixes), width), dtype=np.int64)
            lengths = np.empty(len(prefixes), dtype=np.int64)
            for row, prefix in enumerate(prefixes):
                values[row, :len(prefix)] = prefix + 1
                lengths[row] = len(prefix)
            negatives = _sample_unseen(
                fit.matrix.indptr.astype(np.int64), fit.matrix.indices.astype(np.int64),
                batch_users, n_items, self.seed + epoch * 100_003 + int(batch_users[0]),
            )
            return values, lengths, np.asarray(positives) + 1, negatives + 1

        model.train()
        for epoch in range(self.epochs):
            order = rng.permutation(eligible_users)
            for start in range(0, len(order), self.batch_size):
                batch_users = order[start:start + self.batch_size]
                values, lengths, positives, negatives = make_batch(batch_users, epoch)
                values_t = torch.as_tensor(values, dtype=torch.long, device=device)
                lengths_t = torch.as_tensor(lengths, dtype=torch.long, device=device)
                representation = model.encode(values_t, lengths_t)
                positive_t = torch.as_tensor(positives, dtype=torch.long, device=device)
                negative_t = torch.as_tensor(negatives, dtype=torch.long, device=device)
                positive_scores = (representation * model.items(positive_t)).sum(dim=1)
                negative_scores = (representation * model.items(negative_t)).sum(dim=1)
                loss = torch.nn.functional.softplus(negative_scores - positive_scores).mean()
                optimizer.zero_grad(set_to_none=True)
                loss.backward()
                optimizer.step()

        model.eval()
        all_user_factors = np.zeros((fit.matrix.shape[0], self.factors), dtype=np.float32)
        with torch.no_grad():
            for start in range(0, len(sequences), self.batch_size):
                batch = [seq[-self.max_length:] for seq in
                         sequences[start:start + self.batch_size]]
                lengths = np.asarray([max(1, len(seq)) for seq in batch], dtype=np.int64)
                width = int(lengths.max())
                values = np.zeros((len(batch), width), dtype=np.int64)
                for row, seq in enumerate(batch):
                    if len(seq):
                        values[row, :len(seq)] = seq + 1
                representation = model.encode(
                    torch.as_tensor(values, dtype=torch.long, device=device),
                    torch.as_tensor(lengths, dtype=torch.long, device=device),
                )
                all_user_factors[start:start + len(batch)] = representation.cpu().numpy()
            self.item_factors_ = model.items.weight[1:].detach().cpu().numpy().astype(np.float32)
        self.user_factors_ = all_user_factors
        return self

    def score_user(self, user: int) -> np.ndarray:
        if self.user_factors_ is None or self.item_factors_ is None:
            raise RuntimeError("Call fit before scoring")
        return self.item_factors_ @ self.user_factors_[int(user)]


def time_decayed_matrix(fit, decay: float) -> sparse.csr_matrix:
    """Weight each user-item pair by recency of its last fit-period interaction."""
    last = fit.frame.groupby(["user_idx", "item_idx"], sort=False)["day"].max().reset_index()
    end_day = int(fit.frame["day"].max())
    weights = np.exp(-float(decay) * (end_day - last["day"].to_numpy())).astype(np.float32)
    matrix = sparse.csr_matrix(
        (weights, (last["user_idx"].to_numpy(), last["item_idx"].to_numpy())),
        shape=fit.matrix.shape, dtype=np.float32,
    )
    matrix.sort_indices()
    return matrix
