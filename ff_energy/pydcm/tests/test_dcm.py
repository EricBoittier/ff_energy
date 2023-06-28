import os
import unittest

import pandas as pd

from ff_energy.pydcm.dcm import mdcm, mdcm_set_up, scan_fesp, scan_fdns, \
    mdcm_cxyz, mdcm_clcl, local_pos, get_clcl, optimize_mdcm, eval_kernel
from pathlib import Path
from ff_energy.pydcm import dcm_utils as du
from ff_energy.pydcm.dcm import DCM_PY_PATH
from ff_energy.pydcm.kernel import KernelFit
import matplotlib.pyplot as plt

import warnings
warnings.filterwarnings('ignore')

def ignore_warnings(test_func):
    def do_test(self, *args, **kwargs):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", ResourceWarning)
            test_func(self, *args, **kwargs)
    return do_test


class MyTestCase(unittest.TestCase):
    def test_something(self):
        self.assertEqual(True, False)  # add assertion here

    def get_mdcm(self):
        return mdcm_set_up(scan_fesp, scan_fdns,
                           local_pos=local_pos,
                           mdcm_cxyz=mdcm_cxyz,
                           mdcm_clcl=mdcm_clcl)

    def test_dcm_fortran(self):
        m = mdcm_set_up(scan_fesp, scan_fdns,
                        local_pos=local_pos,
                        mdcm_cxyz=mdcm_cxyz,
                        mdcm_clcl=mdcm_clcl)
        print(m.get_rmse())
        optimize_mdcm(m, m.mdcm_clcl, "", "test")

    def test_load_data(self, l2 = '100.0'):
        PICKLES = list(Path(f"/home/boittier/Documents/phd/ff_energy/cubes/clcl/{l2}")
                       .glob("*.obj"))
        scanpath = Path("/home/boittier/Documents/phd/ff_energy/cubes/dcm/")

        def name_(x):
            if "gaussian" in str(x):
                return scanpath / "scan" / (x.name.split(".c")[0] + ".cube")
            elif "_nms_" in str(x):
                return scanpath / "nms" / (x.name.split(".c")[0] + ".cube")
            else:
                print(f"ValueError(fbad pickle name {x})")
                return None

        PICKLES = [_ for _ in PICKLES if name_(_) is not None]
        CUBES = [name_(_) for _ in PICKLES]
        return du.get_data(CUBES, PICKLES, 5)

    def test_standard_rmse(self, k, files, cubes, pickles):
        cube_paths = Path("/home/boittier/Documents/phd/ff_energy/cubes/dcm/")
        ecube_files = list(cube_paths.glob("*/*esp.cube"))
        dcube_files = list(cube_paths.glob("*/*dens.cube"))
        print("ecube", len(ecube_files))
        print("dcube", len(dcube_files))
        print(len(cubes), len(pickles))
        rmses = eval_kernel(files, ecube_files, dcube_files)
        print("RMSEs:", rmses)
        rmse = sum(rmses) / len(rmses)
        print("RMSE:", rmse)
        k.plot_pca(rmses, title=f"Standard ({rmse:.2f})")
        pd.DataFrame({"rmses": rmses,
                      "filename": files}
                     ).to_csv("standard_.csv")

    def experiments(self):
        alphas = [0.0, 0.1, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0]
        l2s = [0.0, 0.1, 0.5, 1.0, 2.0, 4.0, 8.0]
        N_factors = [2, 4, 6, 8, 10, 12]
        for alpha in alphas:
            for l2 in l2s:
                for N_factor in N_factors:
                    print("alpha", alpha, "l2", l2, "N_factors", N_factors)
                    self.test_fit(alpha=alpha, l2=l2, N_factor=N_factor)

    def test_N_repeats(self, n=5):
        for i in range(n):
            print("i", i)
            self.experiments()

    @ignore_warnings
    def test_fit(self,
                 alpha=0.0,
                 l2=0.0,
                 do_null=True,
                N_factor=2,
                 do_optimize=False
                 ):

        cube_paths = Path("/home/boittier/Documents/phd/ff_energy/cubes/dcm/")
        ecube_files = list(cube_paths.glob("*/*esp.cube"))
        dcube_files = list(cube_paths.glob("*/*dens.cube"))
        print("n_cubes", len(ecube_files))

        m = self.get_mdcm()
        print("mdcm_clcl")
        print(m.mdcm_clcl)

        if do_optimize is False:
            print("Optimizing")
            opt_rmses = eval_kernel(range(140), ecube_files, dcube_files,
                        opt=True, l2=l2)
            print("Opt RMSEs:", opt_rmses)
            opt_rmse = sum(opt_rmses) / len(opt_rmses)
            print("Opt RMSE:", opt_rmse)

        x, i, y, cubes, pickles = self.test_load_data(l2=str(l2))

        k = KernelFit()
        k.set_data(x, i, y, cubes, pickles)
        k.fit(alpha=alpha, N_factor=N_factor)

        print("N X:", len(k.X))
        print("N:", len(k.ids))
        print("N test:", len(k.test_ids))
        print("N_train:", len(k.train_ids))
        print(k.r2s)
        print("sum r2s test:", sum([_[0] for _ in k.r2s]))
        print("sum r2s train:", sum([_[1] for _ in k.r2s]))
        print("n models:", len(k.r2s))

        print("Moving clcls")
        files = k.move_clcls(m.mdcm_clcl)
        print("N files:", len(files), '\n')

        #  test the original model
        if do_null:
            self.test_standard_rmse(k, files, cubes, pickles)

        rmses = eval_kernel(files, ecube_files, dcube_files,
                            load_pkl=True)
        print("RMSEs:", rmses)
        rmse = sum(rmses) / len(rmses)
        print("RMSE:", rmse)

        self.prepare_df(k, rmses, files, alpha=alpha, l2=l2)

        if do_optimize is False:
            self.prepare_df(k, opt_rmses, files, alpha=alpha, l2=l2, opt=True)

        k.plot_fits(rmses)
        k.plot_pca(rmses, title=f"Kernel ({rmse:.2f})", name=f"kernel_{k.uuid}.png")

        if do_optimize is False:
            k.plot_pca(opt_rmses, title=f"Optimized ({opt_rmse:.2f})",
                       name=f"opt_{k.uuid}.png")

    def prepare_df(self, k, rmses, files, alpha=0.0, l2=0.0, opt=False):
        class_name = ["test" if _ in k.test_ids
                      else "train" for _ in k.ids]
        if opt:
            fn = f"opt_{k.uuid}_{l2}.csv"
        else:
            fn = f"kernel_{k.uuid}_{alpha}_{l2}.csv"
        pd.DataFrame(
            {
                "rmse": rmses,
                "pkl": files,
                "class": class_name,
                "alpha": alpha,
                "uuid": k.uuid,
                'l2': l2,
                "type": ["nms" if "nms" in str(_) else "scan"
                         for _ in files]
            }
        ).to_csv(fn)


    def test_files(self):
        i = 4
        l2 = 0.0
        cube_paths = Path("/home/boittier/Documents/phd/ff_energy/cubes/dcm/scan")
        ecube_files = list(cube_paths.glob("*esp.cube"))
        dcube_files = list(cube_paths.glob("*dens.cube"))
        print(len(ecube_files), len(dcube_files))
        ecube_files.sort()
        dcube_files.sort()
        print(ecube_files[0], dcube_files[0])
        #  name of the esp and dens cube files
        e = str(ecube_files[i])
        d = str(dcube_files[i])
        #  set up the mdcm object
        m = mdcm_set_up([e], [d],
                        local_pos=local_pos,
                        mdcm_cxyz=mdcm_cxyz,
                        mdcm_clcl=mdcm_clcl)
        print("RMSE:", m.get_rmse())
        outname = ecube_files[i].name + f"_{l2}"
        optimize_mdcm(m, m.mdcm_clcl, "", outname, l2=l2)


if __name__ == '__main__':
    unittest.main()