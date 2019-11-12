## Build
A simple build can be accomplished cross-platform by running the following python script:

`$> python ./scripts/build.py`

`--help` options will describe how to use the features in the script.

### PREREQUISTS:

1. Jupyter installed
    - Linux: jupyter must be added to the PATH so `$> command -v jupyter` works in terminal
    - Windows: PowerShell must have jupyter installed so `PS C:\> Get-Command jupyter` works

        ***To install Jupyter into PowerShell using Anaconda***
        1. Run `C:\> conda init` from Cmd.exe prompt

        2. Open PowerShell and check is whether or not a profile already exists.

            `PS C:\> Test-Path $profile          # Returns True or False`

        3. If a profile does not exist, run the following to create one.  This will generate a file at `C:\Users\<user>\Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1`

            `New-Item -path $profile -type file –force`

        4. Anaconda installation adds a profile.ps1 file to your `C:\Users\<user>\Documents\WindowsPowerShell\` directory.  In order to enable PowerShell to use this profile, you need to add a command to also load conda's profile.ps1 into your Microsoft.PowerShell_profile.ps1 file.  To do this, Open the default profile with a Text Editor like Notepad.exe.

        `PS C:\> notepad.exe C:\Users\<user>\Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1`

        Add the following to the default profile:

        `. .\profile.ps1`

        This will dot-source the conda controlled profile file into your normal environment so that it will automatically load when PowerShell is loaded.  Save and exit the editor.

        5. To reload your new modified profile without restarting PowerShell:

        `PS C:\> & $profile`

           **If you receive a Scripts Execution Permissions Error,**
       you will have to run the following command first to enable any scripts to run.  This can be a security concern so once you are finished running scripts, you should reverse the command to an execution policy of 'Restricted'

           `PS C:\> Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy Unrestricted`

        6. Now, you should see '(base)' in front of your command prompt which indicates you are in the base conda environment.  Additionally to verify that jupyter is available, run the following command:

        `(base) PS C:\> Get-Command jupyter`
        `(base) PS C:\> python --version`



## DEPLOY APPLICATION (LINUX ONLY)

If you want to deploy straight to Google Compute Engine, Run:

`$> python ./scripts/deploy_vm.py`

`--help` option will describe how to use the script.

### PREREQUISTS:

1. Ansible & Jupyter installed on $PATH
2. Configure `./scripts/ansible/gce_vars/auth` parameters using a service account *.json
3. Configure `./scripts/ansible/group_vars/all` paremeters with ssh account key to service account.
4. Set Administrator password in the file `./scripts/ansible/roles/configure/vars/secrets.yml`
5. `./scripts/build.py` available

## RECALL APPLICATION (LINUX ONLY)
To tear down and release all GCE resources, Run:

`$> python ./scripts/deploy_vm.py --destroy`

This will release all resources except the persistent disk allocation.  Once all resources are released, Google Cloud billing will cease. 


## TROUBLESHOOTING

**NOTES**
1. All filepaths that use `./` above are a relative path from the main project's root directory.

