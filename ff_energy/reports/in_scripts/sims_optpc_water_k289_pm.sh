papermill ../templates/sim_template.ipynb ../out_notebooks/sims_optpc_water_k289.ipynb -k pycharmm -p jobpath  "/home/boittier/pcbach/sims/optpc/water/k289/dynamics.log" -p NSAVC 1000 -p dt 0.0002

jupyter nbconvert --to webpdf --no-input ../out_sims_optpc_water_k289.ipynb 