import os
import re
import shutil
from itertools import product
from multiprocessing import Pool
import subprocess
# import pexpect


def writeoutput_file(destination_file_path, file_params, sectionval, temperature):
    input_file_path = os.getcwd() + "/temp.opts"
    with open(input_file_path, "r") as file:
        content = file.read()
    with open(destination_file_path, 'w') as fp:
        fp.write("parameters " + file_params + "\n")
        fp.write("\n")

    def writelines(input_file_path, line, sectionval=sectionval, temperature=temperature):
        with open(input_file_path, "r") as source_file:
            lines = source_file.readlines()
        start = lines.index(line) + 1
        end = lines[start:].index("))\n") + start

        if line == "model_files_section((\n":
            with open(destination_file_path, "a") as destination_file:
                for l in lines[start:end]:
                    ind = l.find(" section")
                    if ind != -1:
                        l = l[:ind]
                        l = "include " + "\"" + l + "\""
                        destination_file.write(l + " section = " + str(sectionval) + '\n')
                    else:
                        l = "include " + "\"" + l[:-1] + "\""
                        destination_file.write(l + "\n")
                destination_file.write('\n')
        elif line == "simulator_options((\n":
            with open(destination_file_path, "a") as destination_file:
                for l in lines[start:end]:
                    if l.find("temp") != -1:
                        l = l.replace("temp", 'temp=' + temperature)
                        destination_file.write(l)
                    else:
                        destination_file.write(l)
                destination_file.write('\n')
        else:
            with open(destination_file_path, "a") as destination_file:
                destination_file.writelines(lines[start:end])
                destination_file.write("\n")

    ############################################
    # OUTPUT FILE FORMAT
    writelines(input_file_path, "model_files_section((\n")
    ###################
    # line_relatedto_temp = "simulatorOptions options reltol=1e-3 vabstol=1e-6 iabstol=1e-12 temp=" + temp
    # with open(destination_file_path, "a") as fp:
    #     fp.write(line_relatedto_temp + "\n")
    ###################
    writelines(input_file_path, "simulator_options((\n")
    writelines(input_file_path, "analysis_commands((\n")
    writelines(input_file_path, "misc_options((\n")
    ############################################


def returnvalues(file_path):
    with open(file_path, "r") as file:
        data = file.read()
    pattern = r'(\w+)\s*=\s*list\(([^)]+)\)'
    matches = re.findall(pattern, data)
    values = []
    parms = []
    for match in matches:
        value_str = match[1]
        if value_str == '':
            continue
        parm = match[0]
        values.append(value_str)
        parms.append(parm)
    return values, parms


def run(run_cmd_file):
    subprocess.run(["spectre", run_cmd_file])


def main():
    dict = {}
    file_path = os.getcwd() + "/temp.opts"
    with open(file_path, "r") as file:
        content = file.read()
    start = content.find("circuit_parameters((") + len("circuit_parameters((")
    end = content[start:].find("))") + start
    parmslist = content[start:end]
    parmslist = parmslist.replace(" ", "")
    parmslist = parmslist.replace("\n", "")
    parmslist = parmslist.replace("-", "")
    parmslist = parmslist.replace("=", "")
    parmslist = parmslist.replace("list(", "")
    parmslist = parmslist.replace(")", "")
    parmslist = parmslist.replace(",", "")
    parmslist = parmslist.replace(".", "")
    parms = []
    p = ''
    for i in range(len(parmslist)):
        if not parmslist[i].isdigit():
            p = p + parmslist[i]
        else:
            if p != '':
                parms.append(p)
            p = ''

    new = []
    values, parms = returnvalues(file_path)
    for i in range(len(parms)):
        vals = values[i]
        vals = list(vals.split(","))
        new.append(vals)
        dict[parms[i]] = vals
    file_list = list(product(*new))
    file_names = []
    path = os.getcwd()
    sim_dir = path + "/debug_sim_files/"
    if "debug_sim_files" in os.listdir(path):
        shutil.rmtree(sim_dir)
    os.makedirs(sim_dir)
    file_list_raw = []
    nfiles = int(input("enter no of simulations to run:"))
    for i in range(nfiles):
        file_name = ''
        file_parms = ''
        for j in range(len(parms) - 2):
            file_name = file_name + parms[j] + '=' + str(file_list[i][j]) + '@'
            file_parms = file_parms + parms[j] + '=' + str(file_list[i][j]) + '@'
            if j == len(parms) - 3:
                j += 1
                file_name = file_name + parms[j] + '=' + str(file_list[i][j]) + '@'
                j += 1
                file_name = file_name + parms[j] + '=' + str(file_list[i][j]) + '@'
        file_name = file_name.replace('@', ' ')
        file_params = file_parms.replace('@', ' ')
        file_name = file_name.replace('=', '_')
        file_name = file_name.replace(' ', '_')
        file_name = file_name.replace("*", ",")
        file_path = sim_dir + str(file_name) + '.scs'
        writeoutput_file(file_path, file_params, file_list[i][-1], file_list[i][-2])
        file_names.append(file_name)
        file_list[i] = sim_dir + file_name + ".scs"
        file_list_raw.append(file_name + ".raw")
    print(
        file_list_raw)  # ['CL_700n_ILoad_10u_Li_Bond_out_0_RL_13_Resr_0_Rz_0_a_0_b_0_c_0_d_0_e_0_f_0_vdd_1.8_vref_0.4_Lesr_900u,CL_temperature_-40_section_tt_', 'CL_700n_ILoad_10u_Li_Bond_out_0_RL_13_Resr_0_Rz_0_a_0_b_0_c_0_d_0_e_0_f_0_vdd_1.8_vref_0.4_Lesr_900u,CL_temperature_-40_section_ss_',
    # 'CL_700n_ILoad_10u_Li_Bond_out_0_RL_13_Resr_0_Rz_0_a_0_b_0_c_0_d_0_e_0_f_0_vdd_1.8_vref_0.4_Lesr_900u,CL_temperature_-40_section_ff_']

    var_parms = ['CL', 'ILoad', 'Li_Bound_out', 'Rz', 'a']
    var_values = []
    temp_values = []
    corner_values = []
    for i in range(len(file_list_raw)):
        start = file_list_raw[i].index('temperature') + len('temperature') + 1
        end = file_list_raw[i][start:].index('_') + start
        res = file_list_raw[i][start:end]
        temp = "\"" + res + "\" "
        temp_values.append(temp)
        start = file_list_raw[i].index('section') + len('section') + 1
        end = file_list_raw[i][start:].index('_') + start
        res = file_list_raw[i][start:end]
        corner = 'list("' + res + '")'
        corner_values.append(corner)
    print(corner_values, temp_values)
    for file_string in file_list_raw:
        values = []
        for parm in var_parms:
            pattern = parm + r'_([^_]+)_'
            match = re.search(pattern, file_string)
            if match:
                values.append('"' + match.group(1) + '"')
        var_values.append('list(' + ' '.join(values) + ')')
    # var_values
    # temp_values
    # corner_values

    with Pool(3) as p:
        p.map(run, file_list[:nfiles])
    temp_path = os.getcwd() + '/temp.opts'

    # read ocean file from .pots file
    with open(temp_path, "r") as tempfile:
        readocean = tempfile.read()
    start = readocean.find('my_post_precessing_ocn_file((') + len('my_post_precessing_ocn_file((') + 1
    end = readocean[start:].find('))') + start - 1
    ocean_file = readocean[start:end]
    print(ocean_file + '--------------------------------------------------------------------------------------------')
    ocean_cmds = [
        'load "' + ocean_file + '"'
    ]
    for i in range(len(file_list_raw)):
        ocean_cmds.append(
            'my_run("' + file_list_raw[i] + '" ' + '"./output.csv" ' + temp_values[i] + corner_values[i] + ' ' +
            var_values[i] + ')')
    ocean_cmds.append('close(fptr)')
    ocean_cmds.append('exit()')

    with open(sim_dir + 'temptest.ocn', 'w') as file:
        for line in ocean_cmds:
            file.write(line + '\n')
    lines = [
        'import os',
        'os.system("ocean < ' + sim_dir + 'temptest.ocn")'
    ]
    with open(sim_dir + 'ocean_env.py', 'w') as file:
        for line in lines:
            file.write(line + '\n')
    subprocess.run("python3 ocean_env.py", shell=True, cwd=sim_dir)
    # os.system("python3 "+sim_dir+"temptest.py")


#    subprocess.run("ocean", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=sim_dir)

if __name__ == "_main_":
    main()
