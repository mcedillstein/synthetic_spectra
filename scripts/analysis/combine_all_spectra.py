#### Reads in all of the ".dat" files generated by Veeper
#### and combines them into a single file, "all_spectra.h5"

import numpy as np
import glob
import os
import sys
import h5py as h5 

import eqwrange as eqw
import spectrum_analysis_tools as spa

def find_closest_z(z_comp, json_z_list):
    closest_z = -1
    smallest_diff = 1.
    for z in json_z_list:
        diff = abs(z_comp - z)
        if diff < smallest_diff:
            smallest_diff = diff
            closest_z = z
    return closest_z

master_ion_list = ['HI', 'OVI', 'CII', 'CIII', 'SiII', 'SiIII', 'SiIV', 'NV']

work_dir = '../../data/analyzed_spectra'
spec_outfile = h5.File('%s/combined_spectra.h5'%(work_dir), 'w')

model_list   = [];   redshift_list = [];   impact_list = [];     label_list = [];
col_list     = [];     sigcol_list = [];     bval_list = [];   sigbval_list = [];
vel_list     = [];     sigvel_list = [];      ion_list = [];    ray_id_list = []; 
restwave_list = []; flag_aodm_list = [];     flag_list = [];
total_col_list = []; total_colerr_list = [];

# go to the directory where the analyzed spectra reside
os.chdir(work_dir)
dummy = -9999.


spec_files = glob.glob('COS-FUV_*')
#spec_files = glob.glob('COS-FUV_P0_z0.25_72*')

for spec in spec_files:
    print(spec)
    if not os.path.isdir(spec) or not spa.spec_ready_for_analysis(spec):
        print('Skipping %s\n'%(spec))
        continue

    model, redshift, impact, ray_id = spa.extract_spec_info(spec)
    
    veeper_fn = '%s/cleanVPoutput.dat'%(spec)
    json_fn = '%s/%s_lineids.json'%(spec, spec)
    json_out = '%s/json_eqw.dat'%(spec)
    aodm_fn = '%s/%s_ibnorm.fits'%(spec, spec)
    aodm_plot_dir = '%s/aodm_plots'%(spec)
    
    veeper_ions, veeper_restwaves, veeper_cols, veeper_colerr, veeper_bvals, \
        veeper_bvalerr, veeper_vels, veeper_velerr, veeper_label, veeper_z =  eqw.load_veeper_fit(veeper_fn)
    json_ions, json_restwaves, json_cols, json_colerr, json_flag, json_z = \
        eqw.json_eqw(json_fn, aodm_fn, json_out, overwrite = True)

    print(json_ions, json_flag)
    
    for ion in master_ion_list:
        rw = spa.restwave(ion, redshift) 
        # assume the number of components is 1, to start
        num_comps = 1
        mask = (veeper_ions == ion)
        if ion in veeper_ions:
            ncomp = 0
            total_col = 0
            total_sqerr = 0
            for i in range(len(veeper_ions[mask])):
                z_closest = find_closest_z(veeper_z[mask][i], json_z[json_ions == ion])
                if z_closest == -1:
                    print("WARNING: NO Z_CLOSEST: ", spec, json_z[json_ions == ion])
                json_mask = (json_ions == ion) & (json_z == z_closest)
                ncomp += 1
                if 1 in json_flag[json_mask]:
                    col = veeper_cols[mask][i]
                    colerr = veeper_colerr[mask][i]
                    flag = 1
                elif 2 in json_flag[json_mask]:
                    json_mask = (json_ions == ion) & (json_z == z_closest) & (json_flag == 2)
                    col = max(json_cols[json_mask])
                    colerr = 0
                    flag = 2
                elif 3 in json_flag[json_mask]:
                    json_mask = (json_ions == ion) & (json_z == z_closest) &(json_flag == 3)
                    col = min(json_cols[json_mask])
                    colerr = 0
                    flag = 3

                total_col += np.power(10, col)
                total_sqerr += np.power(10, colerr)**2
 
                restwave_list = np.append(restwave_list,  veeper_restwaves[mask][i])
                ion_list      = np.append(ion_list,       ion)
                col_list      = np.append(col_list,       col) 
                sigcol_list   = np.append(sigcol_list, colerr)
            
                bval_list     = np.append(bval_list,      veeper_bvals[mask][i])
                sigbval_list  = np.append(sigbval_list, veeper_bvalerr[mask][i])
                vel_list      = np.append(vel_list,        veeper_vels[mask][i])
                sigvel_list   = np.append(sigvel_list,   veeper_velerr[mask][i])
                label_list    = np.append(label_list,     veeper_label[mask][i])
                flag_list     = np.append(flag_list,    flag)

                impact_list      = np.append(impact_list,     impact)
                model_list       = np.append(model_list,     model)
                ray_id_list      = np.append(ray_id_list,    ray_id)
                redshift_list    = np.append(redshift_list,  redshift)

            total_col_list = np.append(total_col_list, ncomp*[np.log10(total_col)])
            total_colerr_list = np.append(total_colerr_list, ncomp*[np.log10(np.sqrt(total_sqerr))])
        else:

            eqws, sigeqw, lncol, siglncol, flag_aodm, velcent, velwidth = \
                eqw.find_ion_limits(ion, aodm_fn, redshift = redshift, \
                silent = 1, plots = 0, plot_dir = aodm_plot_dir, vrange = (-200, 200), sat_limit = 0.1) 

            restwave_list = np.append(restwave_list,     rw)
            ion_list      = np.append(ion_list,         ion)
            col_list      = np.append(col_list,       lncol)
            sigcol_list   = np.append(sigcol_list, siglncol)
            total_col_list = np.append(total_col_list, siglncol)
            total_colerr_list = np.append(total_colerr_list, siglncol)
            bval_list     = np.append(bval_list,     dummy)
            sigbval_list  = np.append(sigbval_list,  dummy)
            vel_list      = np.append(vel_list,      dummy)
            sigvel_list   = np.append(sigvel_list,   dummy)
            label_list    = np.append(label_list,     "--")
            flag_list     = np.append(flag_list,         3)
            impact_list      = np.append(impact_list,   impact)
            model_list       = np.append(model_list,     model)
            ray_id_list      = np.append(ray_id_list,   ray_id)
            redshift_list    = np.append(redshift_list,  redshift)

 
dataset_names = ['impact', 'ray_id', 'redshift', 'restwave', 'col', 'col_err', 'bval', \
                  'bval_err', 'vel', 'vel_err', 'flag', 'total_col', 'total_col_err']
datasets = [impact_list, ray_id_list, redshift_list, restwave_list, col_list, sigcol_list,\
                bval_list, sigbval_list, vel_list, sigvel_list, flag_list, total_col_list, total_colerr_list]

# first save the numerical data   
for dset, data in zip(dataset_names, datasets):
    print(dset, len(data))
    spec_outfile.create_dataset(dset, data = data)


# then save string-type data in a special way     
dt = h5.special_dtype(vlen=str)
dataset_names = ['model', 'ion', 'label']
datasets = [model_list, ion_list, label_list]
for dset, data in zip(dataset_names, datasets):
    print(dset, len(data))
    current_dset = spec_outfile.create_dataset(dset, (len(data),), dtype=dt)
    for i in range(len(data)):
        current_dset[i] = data[i].replace(" ", "")


spec_outfile.close()
            
                    
                    



