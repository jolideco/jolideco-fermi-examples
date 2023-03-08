rule run_jolideco:
    input:
        filename_datasets="results/{config_name}/datasets/{config_name}-datasets-all.yaml",
        filename_model="results/{config_name}/model/{config_name}-model.yaml",
    log:
        notebook="results/{config_name}/jolideco/{config_name}-jolideco.ipynb"
    output:
        "results/{config_name}/jolideco/{config_name}-result-jolideco.fits",
    notebook:
        "../notebooks/jolideco-deconvolution.ipynb"