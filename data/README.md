# Local research datasets

Raw datasets are not bundled with the application starter. Existing public-source files already versioned in this repository are preserved separately.

Start with the [official MBS datathon releases](https://github.com/mbs-datathon/maldives-datathon-2026-datasets/releases). Extract the datasets into the paths described in [the agent catalogue](../tools/data-catalogue.json). Relevant local layouts are `team-kandu/`, `MACL/MACL/`, `MTCC/`, `Avas_Ride/` and `FollowMe/FollowMe_august_2025/`.

Additional public-source paths and research references are described in the catalogue and [research notes](../research/04_build_feasibility.md). Do not assume availability of a public download means every field is accurate, complete or licensed for redistribution. Review source terms before committing derived data.

An agent can inspect the catalogue without downloading anything:

```powershell
python tools/data_mcp.py --call data_list_datasets
```

Files absent on a new checkout are reported as unavailable. `data_describe_dataset` and `data_sample_rows` inspect locally supplied files only. No raw data is automatically copied into `web/public/`.
