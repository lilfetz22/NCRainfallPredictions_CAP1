# Build
A simple build can be accomplished cross-platform by running the following python script:

`$> python ./scripts/build.py`

`--help` options will describe how to use the features in the script.

## PREREQUISTS:

1. Jupyter installed
    - Linux: jupyter must be added to the PATH so `$> command -v jupyter` works in terminal
    - Windows: PowerShell must have jupyter installed so `PS C:\> Get-Command jupyter` works

        ***To install Jupyter into PowerShell using Anaconda***
        1. Run `PS C:\> conda init` from PowerShell.exe prompt

           **If you receive a Scripts Execution Permissions Error,**
       you will have to run the following command first to enable the conda script to run
       and then reaccomplish step 1.

           `PS C:\> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned`

        2. Restart PowerShell


# DEPLOY APPLICATION (LINUX ONLY)

If you want to deploy straight to Google Compute Engine, Run:

`$> ./scripts/build-vm.sh`

`--help` option will describe how to use the script.

## PREREQUISTS:

1. Ansible & Jupyter installed on $PATH
2. Configure `./scripts/ansible/gce_vars/auth` parameters using a service account *.json
3. Configure `./scripts/ansible/group_vars/all` paremeters with ssh account key to service account.
4. Set Administrator password in the file `./scripts/ansible/roles/configure/vars/secrets.yml`
5. `./scripts/build.py` available

# RECALL APPLICATION (LINUX ONLY)
To tear down and release all GCE resources, Run:

`$> ./scripts/build-vm.sh --destroy`

This will release all resources except the persistent disk allocation.  Once all resources are
released, Google Cloud billing will cease. 

