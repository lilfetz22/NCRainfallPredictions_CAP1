# DevOps Scripts

CapstoneProject1 supports Windows 10, MacOS X, and Linux application compiling and deployment utilizing python3.  Below you will find the commands to build and deploy the application, please make sure to follow all steps especially the Windows-specific configurations.  If you have any problems, please submit a detailed issue report after you have attempted these instructions more than once.

Due to the fact, the Ansible controller does not support the Windows platform, these instructions will facilitate the installation of cygwin, a linux environment compiled for Windows.

For simplicity, the instructions will define the variable `$proj = <project_root_dir>` so all filepaths that use `$proj/` are a symbolic path from the main project's root directory.

----

## BUILD

<details>
  <summary>A simple build can be accomplished cross-platform by running the following python script:</summary>

```bash
$> python $proj/scripts/build.py
```

`--help` options will describe how to use the features in the script.

<details>
  <summary>PREREQUISTS:</summary>

1. Jupyter installed
    - Linux: jupyter must be added to the PATH so `$> command -v jupyter` works in terminal
    - Windows: PowerShell must have jupyter installed so `PS C:\> Get-Command jupyter` works
        
        <details>
            <summary>To install Jupyter into PowerShell using Anaconda</summary>

        1. Run `C:\> conda init` from Cmd.exe prompt

        2. Open PowerShell and check is whether or not a profile already exists.

            ```powershell
            PS C:\> Test-Path $PROFILE          # Returns True or False
            ```

        3. If a profile does not exist, run the following to create one.  This will generate a file at `C:\Users\<user>\Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1`

            ```powershell
            PS C:\> New-Item -Path $PROFILE -Type file –Force
            ```

        4. Anaconda installation adds a profile.ps1 file to your `C:\Users\<user>\Documents\WindowsPowerShell\` directory.  In order to enable PowerShell to use this profile, you need to add a command to also load conda's profile.ps1 into your Microsoft.PowerShell_profile.ps1 file.  To do this, Open the default profile with a Text Editor like Notepad.exe.

            ```powershell
            PS C:\> notepad.exe $HOME\Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1
            ```

            Add the following to the default profile:

            ```powershell
            # Import Conda profile
            . $HOME\Documents\WindowsPowerShell\profile.ps1
            ```

            This will dot-source the conda controlled profile file into your normal environment so that it will automatically load when PowerShell is loaded.  Save and exit the editor.

        5. Tell Windows to trust your new PowerShell profile & Conda's activation script

            ```powershell
            PS C:\> Unblock-File -Path $HOME\Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1
            PS C:\> Unblock-File -Path $HOME\Documents\WindowsPowerShell\profile.ps1
            ```

        6. To enable scripts to be run in PowerShell you will need to enable them with the following command.  Windows blocks script execution by default.  This is sometimes considered a security concern so once you are finished running scripts, you should reverse the command to an execution policy of 'Restricted'

            ```powershell
            PS C:\> Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
            ```

        7. To reload your new modified profile without restarting PowerShell:

            ```powershell
            PS C:\> . $PROFILE
            ```

        8. Now, you should see '(base)' in front of your command prompt which indicates you are in the base conda environment.  Additionally to verify that jupyter is available, run the following command:

            ```powershell
            (base) PS C:\> Get-Command jupyter
            (base) PS C:\> python --version
            ```
        </details>

</details>

</details>



----

## DEPLOY APPLICATION

<details>
  <summary>If you want to deploy straight to Google Compute Engine, Run in Bash/PowerShell:</summary>

```bash
$> python $proj/scripts/deploy_vm.py
```
```powershell
PS C:\> python $proj/scripts/deploy_vm.py
```

`--help` option will describe how to use the script.


<details>
  <summary>PREREQUISTS:</summary>

- <details>
  <summary>MacOSX or Linux</summary>

    1. Ansible & Jupyter installed on $PATH
    2. Configure `$proj/scripts/ansible/gce_vars/auth` parameters using a service account *.json
    3. Configure `$proj/scripts/ansible/group_vars/all` paremeters with ssh account key to service account.
    4. Set Administrator password in the file `$proj/scripts/ansible/roles/configure/vars/secrets.yml`
    5. `$proj/scripts/build.py` available
  </details>

- <details>
  <summary>Windows</summary>

    1. Conda environment enabled therefore Jupyter available on $env:Path
    2. Configure `$proj/scripts/ansible/gce_vars/auth` parameters using a service account *.json
    3. Configure `$proj/scripts/ansible/group_vars/all` paremeters with ssh account key to service account.
    4. Set Administrator password in the file `$proj/scripts/ansible/roles/configure/vars/secrets.yml`
    5. `$proj/scripts/build.py` available
    6. Make sure you have attempted a build with the above instructions to ensure your PowerShell environment is ready.
    7. Run the following command to tell Windows to trust the internal script without prompt.  This is required to allow the deployment script to run uninterrupted by idle mode.  Sleep functionalty will be re-enabled by the end of the deployment script.

        ```powershell
        PS C:\> Unblock-File -Path $proj/scripts/SuspendPowerPlan.ps1
        ```

    8. Install ansible in a cygwin environment

        <details>
           <summary>TO INSTALL Ansible on Windows Cygwin Environment</summary>

        1. Download [Cygwin](https://www.cygwin.com/).
        2. Move the downloaded setup file to `C:\cygwin64\cyg-get\`
        3. Run the Cygwin installation file.
        4. When asked which download source you’d like to use, select “Install from Internet”.
        5. When asked for installation location, set it to, `C:\cygwin64`. **This is required for the cygwin_configure.py and deploy_vm.py scripts to find Cygwin.**
        6. When asked where to install local packages, set it to `C:\cygwin64\cyg-get\`.
        7. Select the method which suits your internet connection type. e.g If you’re not connecting from behind a proxy, select the default "Use System Proxy Settings" or if needed "Direct Connection".
        8. Select a mirror to download your packages from. Any option in the list will do, I choose an USA host usually *.edu.
        9. You’ll then be provided with a list of packages which you can download. Don’t select anything, just click “Next”. Doing so will result in the default applications being installed.
        10. When asking if you want to install dependencies, leave everything as their defaults and click “Next”. This will install everything you need to get Cygwin up and running.
        11. Once installation has completed, double-click the "Cygwin64 Terminal" shortcut from the desktop (MUST DO ON FIRST EXECUTION for proper configuration).  You won't need it for the rest of these instructions after the initial open.
        12. Close the cygwin terminal and open PowerShell to run the cygwin_configure.py configuration script

            ```powershell
            PS C:\> python <project_dir>\scripts\cygwin_configure.py
            ```

        13. Upon completion with no errors, you can now use Ansible through Cygwin.
        
        &nbsp;
        **Note: You may access Cygwin inside of PowerShell with the following:**
        
        ```powershell
        PS C:\> C:\cygwin64\bin\bash.exe --init-file <(echo 'source $HOME/.bash_profile')
        ```

        **Or send a single command to bash from PowerShell:**

        ```powershell
        PS C:\> C:\cygwin64\bin\bash.exe -c 'source $HOME/.bash_profile && <command>'
        ```

        **Special Thanks** to [OZNETNERD](http://www.oznetnerd.com/installing-ansible-windows/) for the foundation of these instructions to install Cygwin 2.877 & Ansible on Microsoft Windows.
        </details>

  </details>

</details>

</details>

----

## RECALL APPLICATION
<details>
  <summary>To tear down and release all GCE resources, Run in Bash/Powershell:</summary>

```bash
$> python $proj/scripts/deploy_vm.py --destroy
```
```powershell
PS C:\> python $proj/scripts/deploy_vm.py --destroy
```

This will release all resources except the persistent disk allocation.  Once all resources are released, Google Cloud billing will cease. 
</details>

----

## TROUBLESHOOTING
<details>
  <summary>NOTES</summary>

2. Check your $env:Path variable in PowerShell, it should have:
3. Check your $PATH variable in cygwin, it should have:

    `PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:"` & A bunch of Windows C:\ directories

</details>

