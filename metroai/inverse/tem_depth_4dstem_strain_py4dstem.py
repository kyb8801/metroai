"""
TEM depth — 4D-STEM strain mapping via py4DSTEM   [YOUR PC; GB data + py4DSTEM]
==============================================================================
Goal (★★★): recover an exx/eyy/exy strain map from a 4D-STEM scan of a SiGe/Si sample,
then compare the alloy-layer strain to the XRD-predicted value. The comparison to a
certified value is what makes it ★★★ (like OCD's NIST library).

HONEST WARNING — this is a 1-2 week effort, not a quick script:
  * 4D-STEM datasets are GB-scale raw diffraction cubes (.dm4/.h5/.emd).
  * py4DSTEM has a real learning curve (probe kernel, Bragg-disk detection, lattice fit).
  * NIST's SiGe strain reference is a PHYSICAL RM (XRD-certified), NOT a downloadable cube.
    Public cubes: py4DSTEM sample data, MAPED (github), Gatan Si/SiGe demo.
  * The STRONGEST version uses YOUR OWN HRTEM/4D-STEM scan — that is real differentiation,
    better than a public set, and it's your home turf.

SETUP:  pip install py4DSTEM
This is a SKELETON — adapt to your py4DSTEM version + dataset (see the official
py4DSTEM strain-mapping tutorial notebook).
"""
import numpy as np
# import py4DSTEM

def strain_map_workflow():
    # 1) load a 4D-STEM datacube
    # datacube = py4DSTEM.import_file("sige_4dstem.dm4")

    # 2) probe kernel for Bragg-disk template matching
    # probe  = datacube.get_vacuum_probe(ROI=(...))
    # kernel = probe.get_kernel(mode="sigmoid", origin=(...), radii=(...))

    # 3) detect Bragg disks at every probe position
    # bragg = datacube.find_Bragg_disks(template=kernel, corrPower=1, sigma=2,
    #                                   edgeBoundary=4, minRelativeIntensity=0.005)

    # 4) strain map; reference = unstrained Si substrate region
    # sm = py4DSTEM.process.strain.StrainMap(braggvectors=bragg)
    # sm.choose_basis_vectors(...)          # g1, g2 from a reference diffraction pattern
    # sm.fit_reference_lattice(ref_ROI=...)  # pure-Si (unstrained) region
    # sm.get_strain()                        # -> e_xx, e_yy, e_xy maps

    # 5) VALIDATE against XRD-certified strain (the ★★★ step)
    # exx_alloy = sm.strain_map["e_xx"][alloy_mask].mean()
    # print(f"measured exx = {exx_alloy:.5f}  vs  XRD-predicted = {xrd_value:.5f}")
    raise NotImplementedError("Fill in with your py4DSTEM version + dataset, then validate vs XRD.")


if __name__ == "__main__":
    print(__doc__)
    print(">> Skeleton only. Best executed on YOUR own SiGe/Si 4D-STEM scan, validated against XRD.")
