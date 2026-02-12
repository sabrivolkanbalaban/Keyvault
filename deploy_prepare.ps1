# KeyVault IIS Deploy Preparation Script
# Run this on your DEVELOPMENT machine to prepare a deploy package

$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$DeployDir = "$ProjectDir\deploy"
$PythonVersion = "3.14.3"
$PythonEmbed = "python-$PythonVersion-embed-amd64"
$PythonZip = "$PythonEmbed.zip"
$PythonUrl = "https://www.python.org/ftp/python/$PythonVersion/$PythonZip"

Write-Host "=== KeyVault Deploy Preparation ===" -ForegroundColor Cyan

# Clean previous deploy
if (Test-Path $DeployDir) { Remove-Item $DeployDir -Recurse -Force }
New-Item -ItemType Directory -Path $DeployDir | Out-Null

# Step 1: Download embedded Python
Write-Host "[1/5] Downloading embedded Python $PythonVersion..." -ForegroundColor Yellow
$PythonDir = "$DeployDir\python"
New-Item -ItemType Directory -Path $PythonDir | Out-Null
Invoke-WebRequest -Uri $PythonUrl -OutFile "$DeployDir\$PythonZip"
Expand-Archive -Path "$DeployDir\$PythonZip" -DestinationPath $PythonDir
Remove-Item "$DeployDir\$PythonZip"

# Step 2: Enable pip in embedded Python (uncomment import site)
Write-Host "[2/5] Configuring embedded Python..." -ForegroundColor Yellow
$pthFile = Get-ChildItem "$PythonDir\python*._pth" | Select-Object -First 1
$content = Get-Content $pthFile.FullName
$content = $content -replace '#import site', 'import site'
# Add Lib\site-packages path
$content += "Lib\site-packages"
Set-Content $pthFile.FullName $content

# Install pip
Invoke-WebRequest -Uri "https://bootstrap.pypa.io/get-pip.py" -OutFile "$PythonDir\get-pip.py"
& "$PythonDir\python.exe" "$PythonDir\get-pip.py" --no-warn-script-location
Remove-Item "$PythonDir\get-pip.py"

# Step 3: Install dependencies into embedded Python
Write-Host "[3/5] Installing dependencies..." -ForegroundColor Yellow
& "$PythonDir\python.exe" -m pip install -r "$ProjectDir\requirements.txt" --no-warn-script-location

# Step 4: Copy application files
Write-Host "[4/5] Copying application files..." -ForegroundColor Yellow
$AppDir = "$DeployDir\app"

# Copy app code
Copy-Item "$ProjectDir\app" -Destination "$DeployDir\app" -Recurse
Copy-Item "$ProjectDir\migrations" -Destination "$DeployDir\migrations" -Recurse
Copy-Item "$ProjectDir\wsgi.py" -Destination "$DeployDir\wsgi.py"
Copy-Item "$ProjectDir\run.py" -Destination "$DeployDir\run.py"
Copy-Item "$ProjectDir\requirements.txt" -Destination "$DeployDir\requirements.txt"
Copy-Item "$ProjectDir\.env.example" -Destination "$DeployDir\.env.example"

# Create logs and instance directories
New-Item -ItemType Directory -Path "$DeployDir\logs" -Force | Out-Null
New-Item -ItemType Directory -Path "$DeployDir\instance" -Force | Out-Null

# Step 5: Create web.config with correct paths
Write-Host "[5/5] Creating web.config..." -ForegroundColor Yellow
$webConfig = @'
<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <system.webServer>
    <handlers>
      <add name="httpPlatformHandler"
           path="*"
           verb="*"
           modules="httpPlatformHandler"
           resourceType="Unspecified" />
    </handlers>

    <httpPlatform processPath="%SITE_DIR%\python\python.exe"
                  arguments="%SITE_DIR%\wsgi.py"
                  startupTimeLimit="60"
                  startupRetryCount="3"
                  stdoutLogEnabled="true"
                  stdoutLogFile="%SITE_DIR%\logs\stdout">
      <environmentVariables>
        <environmentVariable name="PORT" value="%HTTP_PLATFORM_PORT%" />
      </environmentVariables>
    </httpPlatform>
  </system.webServer>
</configuration>
'@
Set-Content "$DeployDir\web.config" $webConfig

Write-Host ""
Write-Host "=== Deploy package ready at: $DeployDir ===" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps on the IIS SERVER:" -ForegroundColor Cyan
Write-Host "  1. Copy the 'deploy' folder to C:\inetpub\KeyVault"
Write-Host "  2. Edit web.config: replace %SITE_DIR% with C:\inetpub\KeyVault"
Write-Host "  3. Copy .env.example to .env and fill in your settings"
Write-Host "  4. Run: python\python.exe -m flask db upgrade"
Write-Host "  5. Create IIS site pointing to C:\inetpub\KeyVault"
Write-Host "  6. Set App Pool identity permissions on the folder"
