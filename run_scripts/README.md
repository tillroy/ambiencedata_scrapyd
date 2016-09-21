## Base preparations
System based on users policy, that why to make separate user is necessity.
All files and folders have to be under defined user, **including files below**.

Next files should separately use:
- runpcr
- pcr.conf
- pcr.service

### runpcr
Bash script for lunching server under python virtual environment.
Should be stored **at the same level as server root directory**
```
folder
    |___server_root_folder
    |___runpcr
```

>make file executable **chmod a+x**

>setup absolute path to the python virtual environment and to the server lunching script

### pcr.conf
Contain main settings for server instance

Stored at:
```
/etc/pcr/pcr.conf
```

### pcr.service
**Systemd** unit file for auto run server as a daemon

Stored at:
```
/etc/systemd/system/pcr.service
```
>setup **User** and absolute path to **runpcr** file.