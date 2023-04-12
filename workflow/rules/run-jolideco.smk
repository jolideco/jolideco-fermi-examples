rule run_jolideco:
    input:
        expand("results/{{config_name}}/jolideco/input/{{config_name}}-{event_type}-maps.fits", event_type=config["fermi-lat-data"]["event_types"]),
    log:
        notebook="results/{config_name}/jolideco/{config_name}-jolideco.ipynb"
    output:
        filename_jolideco_result="results/{config_name}/jolideco/{config_name}-result-jolideco.fits",
        expand("results/{{config_name}}/jolideco/npred/{{config_name}}-{event_type}-npred.fits", event_type=config["fermi-lat-data"]["event_types"]),
    notebook:
        "../notebooks/jolideco-deconvolution.ipynb"