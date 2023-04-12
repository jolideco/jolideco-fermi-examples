rule prepare_datasets:
    input:
        filename_datasets="results/{config_name}/datasets/{config_name}-datasets-all.yaml",
        filename_model="results/{config_name}/model/{config_name}-model.yaml",
    output:
        expand("results/{{config_name}}/jolideco/input/{{config_name}}-{event_type}-maps.fits", event_type=config["fermi-lat-data"]["event_types"]),
    script:
        "../scripts/prepare-datasets.py"