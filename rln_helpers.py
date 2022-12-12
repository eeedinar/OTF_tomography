#!/programs/x86_64-linux/python/3.7.0/bin.capsules/python
import logging
import os
import re
import subprocess

from star_helpers import *


def strbool(string):
    if string == "True":
        return True
    elif string == "False":
        return False
    # elif string == "1":
    #     return True
    # elif string == "0":
    #     return False
    else:
        return string


def rln_success(args):
    subprocess.run(f'touch {args.o}RELION_JOB_EXIT_SUCCESS', shell=True)


def rln_failure(args):
    subprocess.run(f'touch {args.o}RELION_JOB_EXIT_FAILURE', shell=True)


def rln_abortcheck(args):
    if os.path.isfile(f"{args.o}RELION_JOB_ABORT_NOW") or os.path.isfile(f"{args.o}RELION_JOB_EXIT_FAILURE"):
        subprocess.run(f"touch {args.o}RELION_JOB_EXIT_ABORTED", shell=True)
        return 1
    return 0


def rln_alias(args, alias, secondary=False):

    if re.findall(".+/job\d+", args.o):

        with open('default_pipeline.star', "r+") as f:
            text = f.read()

        pipeline_str = re.findall(f"{args.o}.+None", text)
        if pipeline_str == []:
            return
        else:
            pipeline_str = pipeline_str[0]
            alias_job = args.o.replace("External", alias)
            formatted_str = pipeline_str.replace("None", alias_job)
            text = text.replace(pipeline_str, formatted_str)

            with open('default_pipeline.star', "w+") as f:
                f.write(text)

            if not os.path.isdir(alias):
                os.system(f"ln -s External/ {alias}")
                if not os.path.isdir(f"{alias}/{alias}") and secondary:
                    jobnum = re.findall("job\d+", args.o)[0]
                    os.system(f"ln -s {jobnum} {alias}/{alias}")
                    

def rln_init_log(args):
    formatter = logging.Formatter('%(asctime)s [%(funcName)s]: %(message)s', datefmt='[%I:%M%p]')

    log_out = logging.getLogger('out')
    log_out.setLevel(logging.INFO)
    handler_out = logging.FileHandler(f'{args.o}run.out', mode='a+')
    handler_out.setFormatter(formatter)
    log_out.addHandler(handler_out)

    log_err = logging.getLogger('err')
    log_err.setLevel(logging.INFO)
    handler_err = logging.FileHandler(f'{args.o}run.err', mode='a+')
    handler_err.setFormatter(formatter)
    log_err.addHandler(handler_err)

    return log_out, log_err


def rln_schemevar(scheme, varname, value, reset_value, vartype=None):
    filepath = f"Schemes/{scheme}/scheme.star"
    # scheme_general, scheme_floats, scheme_bools, scheme_strings, scheme_operators, scheme_jobs, scheme_edges
    dfs = load_starfile(filepath)

    df_dict = {float: dfs[1], bool: dfs[2], str: dfs[3]}
    name_col = {
        float: '_rlnSchemeFloatVariableName',
        bool: '_rlnSchemeBooleanVariableName',
        str: '_rlnSchemeStringVariableName'
    }
    value_col = {
        float: '_rlnSchemeFloatVariableValue',
        bool: '_rlnSchemeBooleanVariableValue',
        str: '_rlnSchemeStringVariableValue'
    }
    reset_col = {
        float: '_rlnSchemeFloatVariableResetValue',
        bool: '_rlnSchemeBooleanVariableResetValue',
        str: '_rlnSchemeStringVariableResetValue'
    }

    condition = lambda dtype, varname: df_dict[dtype][name_col[dtype]] == varname
    if not vartype:
        # print("none-type:")
        for vartype in [float, bool, str]:
            if condition(vartype, varname).sum():
                df_dict[vartype].loc[condition(vartype, varname), value_col[vartype]] = value
                if reset_value != None:
                    df_dict[vartype].loc[condition(vartype, varname), reset_col[vartype]] = reset_value
                write_starfile(dfs, filepath, formatted=[1, 1, 1, 1, 1, 1, 0])
                return True

    if condition(vartype, varname).sum():
        df_dict[vartype].loc[condition(vartype, varname), value_col[vartype]] = value
        df_dict[vartype].loc[condition(vartype, varname), reset_col[vartype]] = reset_value
        write_starfile(dfs, filepath, formatted=[1, 1, 1, 1, 1, 1, 0])
        return True

    return False


def rln_jobvar(scheme, jobname, varname, value):
    filepath = f"Schemes/{scheme}/{jobname}/job.star"
    header, options = load_starfile(filepath)

    condition = lambda varname: options['_rlnJobOptionVariable'] == varname
    if condition(varname).sum():
        options.loc[condition(varname), '_rlnJobOptionValue'] = value

        write_starfile([header, options], filepath)
        return True
    else:
        return False


def rln_liveoutput(args, cmd):
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    while True:
        std_output = process.stdout.readline()
        std_error = process.stderr.readline()
        if process.poll() is not None and std_output == '' and std_error == '':
            break
        if std_output:
            args.log_out.info(std_output.strip())
        if std_error:
            args.log_err.info(std_error.strip())
    return process.poll()