papermill ../templates/sim_template.ipynb ../out_notebooks/sims_optpc_water_k325.ipynb -k pycharmm -p jobpath  "/home/boittier/pcbach/sims/optpc/water/k325/dynamics.log" -p NSAVC 1000 -p dt 0.0002

jupyter nbconvert --to webpdf --no-input ../out_sims_optpc_water_k325.ipynb 