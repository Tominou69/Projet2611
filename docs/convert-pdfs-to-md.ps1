# Script PowerShell pour convertir les PDFs en Markdown via WSL
# Assurez-vous d'avoir installé poppler-utils et pandoc dans WSL

Write-Host "Conversion des PDFs en Markdown..." -ForegroundColor Green

# Liste des fichiers PDF
$pdfFiles = @("aide-tp.pdf", "projet.pdf", "tutoriel-bdw-server.pdf")

foreach ($pdf in $pdfFiles) {
    $baseName = [System.IO.Path]::GetFileNameWithoutExtension($pdf)
    $mdFile = "$baseName.md"
    
    Write-Host "`nTraitement de $pdf..." -ForegroundColor Yellow
    
    # Convertir PDF en texte puis en markdown via WSL
    wsl bash -c "cd /home/fneuf/projects/docs && pdftotext '$pdf' - | pandoc -f plain -t markdown -o '$mdFile'"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ $mdFile créé avec succès" -ForegroundColor Green
    } else {
        Write-Host "✗ Erreur lors de la conversion de $pdf" -ForegroundColor Red
    }
}

Write-Host "`nConversion terminée !" -ForegroundColor Green
Write-Host "Note: Si vous obtenez des erreurs, installez d'abord les outils nécessaires avec:" -ForegroundColor Cyan
Write-Host "wsl bash -c 'sudo apt update && sudo apt install -y poppler-utils pandoc'" -ForegroundColor Cyan

