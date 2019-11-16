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

            `PS C:\> New-Item -path $profile -type file –force`

        4. Anaconda installation adds a profile.ps1 file to your `C:\Users\<user>\Documents\WindowsPowerShell\` directory.  In order to enable PowerShell to use this profile, you need to add a command to also load conda's profile.ps1 into your Microsoft.PowerShell_profile.ps1 file.  To do this, Open the default profile with a Text Editor like Notepad.exe.

            `PS C:\> notepad.exe C:\Users\<user>\Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1`

            Add the following to the default profile:

            `. $HOME\Documents\WindowsPowerShell\profile.ps1`

            This will dot-source the conda controlled profile file into your normal environment so that it will automatically load when PowerShell is loaded.  Save and exit the editor.

        5. Tell Windows to trust your new PowerShell profile & Conda's activation script

            `PS C:\> Unblock-File -Path $home\Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1`
            `PS C:\> Unblock-File -Path $home\Documents\WindowsPowerShell\profile.ps1`

        6. To enable scripts to be run in PowerShell you will need to enable them with the following command.  Windows blocks script execution by default.  This is sometimes considered a security concern so once you are finished running scripts, you should reverse the command to an execution policy of 'Restricted'

            `PS C:\> Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`

        7. To reload your new modified profile without restarting PowerShell:

            `PS C:\> & $profile`

        8. Now, you should see '(base)' in front of your command prompt which indicates you are in the base conda environment.  Additionally to verify that jupyter is available, run the following command:

            `(base) PS C:\> Get-Command jupyter`
            `(base) PS C:\> python --version`



## DEPLOY APPLICATION (LINUX USERS)

If you want to deploy straight to Google Compute Engine, Run:

`$> python ./scripts/deploy_vm.py`

`--help` option will describe how to use the script.

### PREREQUISTS:

1. Ansible & Jupyter installed on $PATH
2. Configure `./scripts/ansible/gce_vars/auth` parameters using a service account *.json
3. Configure `./scripts/ansible/group_vars/all` paremeters with ssh account key to service account.
4. Set Administrator password in the file `./scripts/ansible/roles/configure/vars/secrets.yml`
5. `./scripts/build.py` available

## RECALL APPLICATION (LINUX USERS)
To tear down and release all GCE resources, Run:

`$> python ./scripts/deploy_vm.py --destroy`

This will release all resources except the persistent disk allocation.  Once all resources are released, Google Cloud billing will cease. 

----

## DEPLOY APPLICATION (WINDOWS USERS)

If you want to deploy straight to Google Compute Engine, Open Powershell & run:

`PS C:\> python ./scripts/deploy_vm.py`

`--help` option will describe how to use the script.

### PREREQUISTS:

1. Conda environment enabled therefore Jupyter available on $env:Path
2. Configure `./scripts/ansible/gce_vars/auth` parameters using a service account *.json
3. Configure `./scripts/ansible/group_vars/all` paremeters with ssh account key to service account.
4. Set Administrator password in the file `./scripts/ansible/roles/configure/vars/secrets.yml`
5. `./scripts/build.py` available
6. Make sure you have attempted a build with the above instructions to ensure your PowerShell environment is ready.
7. Run the following command to tell Windows to trust the internal script without prompt.  This is required to allow the deployment script to run uninterrupted by idle mode.  Sleep functionalty will be re-enabled by the end of the deployment script.

    `PS C:\> Unblock-File -Path ./scripts/SuspendPowerPlan.ps1`

8. Install ansible in a cygwin environment

    **TO INSTALL Ansible on Windows Cygwin Environment**

    1. Follow the instructions @ http://www.oznetnerd.com/installing-ansible-windows/
    2. Make sure to use the same installation location of `C:\cygwin64\` so the deploy script will be able to find the application
    2. Make sure to install the dependencies that ansible requires and install ansible using pip
    3. Restart the cygwin application and verify `command -v ansible; [ $? == 0 ] && echo installed || echo "ansible: Not Found"`

## RECALL APPLICATION (WINDOWS USERS)
To tear down and release all GCE resources, Run in PowerShell:

`PS C:\> python ./scripts/deploy_vm.py --destroy`

This will release all resources except the persistent disk allocation.  Once all resources are released, Google Cloud billing will cease. 


## TROUBLESHOOTING

**NOTES**
1. All filepaths that use `./` above are a relative path from the main project's root directory.

