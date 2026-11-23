# Complete-dataset rerun protocol

The complete Twitch file is far larger than the 100k benchmark: millions of users
and potentially hundreds of millions of rows. On this machine (7.5 GiB RAM), an
exact all-user BPR factor matrix plus exact 465k-channel ranking for every user is not
computationally meaningful or memory-safe.

The rerun therefore uses the complete file in a reproducible streaming design:

1. Scan and validate every compressed source row.
2. Record full-file row/user/channel/day statistics.
3. Compute final-fit and recent distinct-viewer channel popularity from all users.
4. Select users independently with stable `blake2b(seed:user_id) % 155 == 0` hashing.
5. Preserve every interaction for selected users and run the identical leakage-safe
   70/15/15 experiment, full hyperparameter grid, and unsampled cohort test.
6. Write results separately under `outputs_full/`; do not overwrite the original
   official-100k results.

This is an independent user-cohort robustness rerun drawn from the full file. The
personalized CF/BPR models are fitted on the selected cohort, while full-file global
statistics and popularity are retained separately. Results must not be described as
exact training or ranking over all full-dataset users.
