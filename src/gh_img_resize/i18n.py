"""In-app localization for the desktop UI."""

from __future__ import annotations

import json
import locale
import os
import sys
from pathlib import Path

APP_DIR_NAME = "gh-img-resize"
SETTINGS_FILENAME = "settings.json"
DEFAULT_LANGUAGE = "en"

# Display order required by the product issue: EN, ES, DE, FR, IT, PT-BR, JA, KO, ZH-CN.
LANGUAGE_ORDER: tuple[str, ...] = (
    "en",
    "es",
    "de",
    "fr",
    "it",
    "pt-BR",
    "ja",
    "ko",
    "zh-CN",
)
SWITCHER_CODES: tuple[str, ...] = (
    "EN",
    "ES",
    "DE",
    "FR",
    "IT",
    "PT-BR",
    "JA",
    "KO",
    "ZH-CN",
)
CODE_BY_SWITCHER = dict(zip(SWITCHER_CODES, LANGUAGE_ORDER, strict=True))
SWITCHER_BY_CODE = dict(zip(LANGUAGE_ORDER, SWITCHER_CODES, strict=True))

SUPPORTED_LANGUAGES = frozenset(LANGUAGE_ORDER)

_EN: dict[str, str] = {
    "window.title": "GitHub image to 999 KB",
    "header.title": "GitHub image to 999 KB",
    "header.subtitle": (
        "Choose an image. Aspect ratio and format stay the same.\n"
        "The saved file is exactly 999 KB (999,000 bytes),\n"
        "under GitHub's 1 MB limit (1,000,000 bytes)."
    ),
    "language.label": "Language",
    "button.choose": "Choose image…",
    "button.save": "Save as 999 KB…",
    "preview.empty": "No image selected yet",
    "info.choose_prompt": "Please choose an image.",
    "dialog.images": "Images",
    "dialog.jpeg": "JPEG",
    "dialog.png": "PNG",
    "dialog.gif": "GIF",
    "dialog.webp": "WebP",
    "dialog.all_files": "All files",
    "error.unsupported_format_title": "Unsupported format",
    "error.unsupported_format_body": "Please choose JPEG, PNG, GIF, or WebP.",
    "error.load_failed_title": "Could not load image",
    "info.selected": (
        "File: {name}\n"
        "Format: {fmt}  |  Size: {width} × {height} px\n"
        "Current size: {bytes:,} bytes ({kb:.1f} KB)\n"
        "Target size: {target:,} bytes (999 KB, under 1,000,000 bytes)"
    ),
    "status.ready": "Ready to save.",
    "progress.resizing": "Adjusting the file…",
    "success.saved": "Saved: {name}",
    "success.result": "Result: {size:,} bytes (999 KB)",
    "success.dimensions": "Dimensions: {width} × {height} px",
    "success.format": "Format: {fmt}",
    "success.scaled": "Resolution was reduced while keeping the aspect ratio.",
    "success.padded": "The original file was smaller than 999 KB and was only padded.",
    "info.saved_file": (
        "Saved file: {path}\nSize: {size:,} bytes\nDimensions: {width} × {height} px"
    ),
    "dialog.done_title": "Done",
    "dialog.done_body": "The file is exactly {size:,} bytes.",
    "status.error": "Error: {message}",
    "error.resize_failed_title": "Adjustment failed",
    "error.cannot_fit_title": "Could not fit the image to 999 KB",
    "progress.loading": "Loading image…",
    "progress.padding": "File is smaller than 999 KB — padding only…",
    "progress.adjusting": "Adjusting size and quality…",
    "progress.scaling": "Reducing resolution while keeping the aspect ratio…",
    "error.target_over_limit": "Target must stay under GitHub's 1 MB limit (1,000,000 bytes)",
    "error.unsupported_suffix": "Unsupported image format: {suffix}",
    "error.cannot_pad": "Could not pad the encoded image to exactly 999 KB",
    "error.detect_format": "Could not detect image format",
    "error.cannot_shrink": "Could not shrink the image to 999 KB",
    "error.encoded_too_large": "Encoded image is larger than the 999 KB target",
    "error.jpeg_eoi": "JPEG end marker not found",
    "error.not_png": "Not a PNG file",
    "error.png_iend": "PNG IEND chunk not found",
    "error.gif_trailer": "GIF trailer not found",
    "error.not_webp": "Not a WebP file",
    "error.unsupported_encode_format": "Unsupported image format: {fmt}",
}

_ES: dict[str, str] = {
    "window.title": "Imagen de GitHub a 999 KB",
    "header.title": "Imagen de GitHub a 999 KB",
    "header.subtitle": (
        "Elige una imagen. La proporción y el formato se conservan.\n"
        "El archivo guardado tiene exactamente 999 KB (999 000 bytes),\n"
        "por debajo del límite de 1 MB de GitHub (1 000 000 bytes)."
    ),
    "language.label": "Idioma",
    "button.choose": "Elegir imagen…",
    "button.save": "Guardar como 999 KB…",
    "preview.empty": "Aún no hay ninguna imagen seleccionada",
    "info.choose_prompt": "Elige una imagen.",
    "dialog.images": "Imágenes",
    "dialog.jpeg": "JPEG",
    "dialog.png": "PNG",
    "dialog.gif": "GIF",
    "dialog.webp": "WebP",
    "dialog.all_files": "Todos los archivos",
    "error.unsupported_format_title": "Formato no compatible",
    "error.unsupported_format_body": "Elige JPEG, PNG, GIF o WebP.",
    "error.load_failed_title": "No se pudo cargar la imagen",
    "info.selected": (
        "Archivo: {name}\n"
        "Formato: {fmt}  |  Tamaño: {width} × {height} px\n"
        "Tamaño actual: {bytes:,} bytes ({kb:.1f} KB)\n"
        "Tamaño objetivo: {target:,} bytes (999 KB, menos de 1 000 000 bytes)"
    ),
    "status.ready": "Listo para guardar.",
    "progress.resizing": "Ajustando el archivo…",
    "success.saved": "Guardado: {name}",
    "success.result": "Resultado: {size:,} bytes (999 KB)",
    "success.dimensions": "Dimensiones: {width} × {height} px",
    "success.format": "Formato: {fmt}",
    "success.scaled": "Se redujo la resolución manteniendo la proporción.",
    "success.padded": "El archivo original era menor de 999 KB y solo se rellenó.",
    "info.saved_file": (
        "Archivo guardado: {path}\nTamaño: {size:,} bytes\nDimensiones: {width} × {height} px"
    ),
    "dialog.done_title": "Listo",
    "dialog.done_body": "El archivo tiene exactamente {size:,} bytes.",
    "status.error": "Error: {message}",
    "error.resize_failed_title": "Error al ajustar",
    "error.cannot_fit_title": "No se pudo ajustar la imagen a 999 KB",
    "progress.loading": "Cargando imagen…",
    "progress.padding": "El archivo es menor de 999 KB: solo se rellena…",
    "progress.adjusting": "Ajustando tamaño y calidad…",
    "progress.scaling": "Reduciendo la resolución y manteniendo la proporción…",
    "error.target_over_limit": "El objetivo debe quedar por debajo del límite de 1 MB de GitHub (1 000 000 bytes)",
    "error.unsupported_suffix": "Formato de imagen no compatible: {suffix}",
    "error.cannot_pad": "No se pudo rellenar la imagen codificada a exactamente 999 KB",
    "error.detect_format": "No se pudo detectar el formato de la imagen",
    "error.cannot_shrink": "No se pudo reducir la imagen a 999 KB",
    "error.encoded_too_large": "La imagen codificada supera el objetivo de 999 KB",
    "error.jpeg_eoi": "No se encontró el marcador final JPEG",
    "error.not_png": "No es un archivo PNG",
    "error.png_iend": "No se encontró el bloque IEND de PNG",
    "error.gif_trailer": "No se encontró el final del GIF",
    "error.not_webp": "No es un archivo WebP",
    "error.unsupported_encode_format": "Formato de imagen no compatible: {fmt}",
}

_DE: dict[str, str] = {
    "window.title": "GitHub Bild auf 999 KB",
    "header.title": "GitHub Bild auf 999 KB",
    "header.subtitle": (
        "Bild wählen. Seitenverhältnis und Format bleiben erhalten.\n"
        "Die gespeicherte Datei ist genau 999 KB (999.000 Bytes),\n"
        "unter GitHubs 1-MB-Limit (1.000.000 Bytes)."
    ),
    "language.label": "Sprache",
    "button.choose": "Bild auswählen…",
    "button.save": "Als 999 KB speichern…",
    "preview.empty": "Noch kein Bild gewählt",
    "info.choose_prompt": "Bitte ein Bild auswählen.",
    "dialog.images": "Bilder",
    "dialog.jpeg": "JPEG",
    "dialog.png": "PNG",
    "dialog.gif": "GIF",
    "dialog.webp": "WebP",
    "dialog.all_files": "Alle Dateien",
    "error.unsupported_format_title": "Nicht unterstütztes Format",
    "error.unsupported_format_body": "Bitte JPEG, PNG, GIF oder WebP wählen.",
    "error.load_failed_title": "Bild konnte nicht geladen werden",
    "info.selected": (
        "Datei: {name}\n"
        "Format: {fmt}  |  Maße: {width} × {height} px\n"
        "Aktuelle Größe: {bytes:,} Bytes ({kb:.1f} KB)\n"
        "Zielgröße: {target:,} Bytes (999 KB, unter 1.000.000 Bytes)"
    ),
    "status.ready": "Bereit zum Speichern.",
    "progress.resizing": "Datei wird angepasst…",
    "success.saved": "Gespeichert: {name}",
    "success.result": "Ergebnis: {size:,} Bytes (999 KB)",
    "success.dimensions": "Maße: {width} × {height} px",
    "success.format": "Format: {fmt}",
    "success.scaled": "Die Auflösung wurde bei gleichem Seitenverhältnis reduziert.",
    "success.padded": "Die Originaldatei war kleiner als 999 KB und wurde nur aufgefüllt.",
    "info.saved_file": (
        "Gespeicherte Datei: {path}\nGröße: {size:,} Bytes\nMaße: {width} × {height} px"
    ),
    "dialog.done_title": "Fertig",
    "dialog.done_body": "Die Datei ist genau {size:,} Bytes groß.",
    "status.error": "Fehler: {message}",
    "error.resize_failed_title": "Anpassung fehlgeschlagen",
    "error.cannot_fit_title": "Bild konnte nicht auf 999 KB gebracht werden",
    "progress.loading": "Bild wird geladen…",
    "progress.padding": "Datei ist kleiner als 999 KB — es wird nur aufgefüllt…",
    "progress.adjusting": "Größe und Qualität werden angepasst…",
    "progress.scaling": "Auflösung wird bei gleichem Seitenverhältnis reduziert…",
    "error.target_over_limit": "Das Ziel muss unter GitHubs 1-MB-Limit (1.000.000 Bytes) bleiben",
    "error.unsupported_suffix": "Nicht unterstütztes Bildformat: {suffix}",
    "error.cannot_pad": "Das kodierte Bild konnte nicht auf genau 999 KB aufgefüllt werden",
    "error.detect_format": "Bildformat konnte nicht erkannt werden",
    "error.cannot_shrink": "Das Bild konnte nicht auf 999 KB verkleinert werden",
    "error.encoded_too_large": "Das kodierte Bild ist größer als das 999-KB-Ziel",
    "error.jpeg_eoi": "JPEG-Endmarkierung nicht gefunden",
    "error.not_png": "Keine PNG-Datei",
    "error.png_iend": "PNG-IEND-Chunk nicht gefunden",
    "error.gif_trailer": "GIF-Trailer nicht gefunden",
    "error.not_webp": "Keine WebP-Datei",
    "error.unsupported_encode_format": "Nicht unterstütztes Bildformat: {fmt}",
}

_FR: dict[str, str] = {
    "window.title": "Image GitHub à 999 Ko",
    "header.title": "Image GitHub à 999 Ko",
    "header.subtitle": (
        "Choisissez une image. Le ratio et le format sont conservés.\n"
        "Le fichier enregistré fait exactement 999 Ko (999 000 octets),\n"
        "sous la limite de 1 Mo de GitHub (1 000 000 octets)."
    ),
    "language.label": "Langue",
    "button.choose": "Choisir une image…",
    "button.save": "Enregistrer en 999 Ko…",
    "preview.empty": "Aucune image sélectionnée",
    "info.choose_prompt": "Veuillez choisir une image.",
    "dialog.images": "Images",
    "dialog.jpeg": "JPEG",
    "dialog.png": "PNG",
    "dialog.gif": "GIF",
    "dialog.webp": "WebP",
    "dialog.all_files": "Tous les fichiers",
    "error.unsupported_format_title": "Format non pris en charge",
    "error.unsupported_format_body": "Veuillez choisir JPEG, PNG, GIF ou WebP.",
    "error.load_failed_title": "Impossible de charger l’image",
    "info.selected": (
        "Fichier : {name}\n"
        "Format : {fmt}  |  Dimensions : {width} × {height} px\n"
        "Taille actuelle : {bytes:,} octets ({kb:.1f} Ko)\n"
        "Taille cible : {target:,} octets (999 Ko, sous 1 000 000 octets)"
    ),
    "status.ready": "Prêt à enregistrer.",
    "progress.resizing": "Ajustement du fichier…",
    "success.saved": "Enregistré : {name}",
    "success.result": "Résultat : {size:,} octets (999 Ko)",
    "success.dimensions": "Dimensions : {width} × {height} px",
    "success.format": "Format : {fmt}",
    "success.scaled": "La résolution a été réduite en conservant le ratio.",
    "success.padded": "Le fichier d’origine faisait moins de 999 Ko et a seulement été complété.",
    "info.saved_file": (
        "Fichier enregistré : {path}\nTaille : {size:,} octets\nDimensions : {width} × {height} px"
    ),
    "dialog.done_title": "Terminé",
    "dialog.done_body": "Le fichier fait exactement {size:,} octets.",
    "status.error": "Erreur : {message}",
    "error.resize_failed_title": "Échec de l’ajustement",
    "error.cannot_fit_title": "Impossible d’ajuster l’image à 999 Ko",
    "progress.loading": "Chargement de l’image…",
    "progress.padding": "Le fichier fait moins de 999 Ko — complément uniquement…",
    "progress.adjusting": "Ajustement de la taille et de la qualité…",
    "progress.scaling": "Réduction de la résolution en conservant le ratio…",
    "error.target_over_limit": "La cible doit rester sous la limite de 1 Mo de GitHub (1 000 000 octets)",
    "error.unsupported_suffix": "Format d’image non pris en charge : {suffix}",
    "error.cannot_pad": "Impossible de compléter l’image encodée à exactement 999 Ko",
    "error.detect_format": "Impossible de détecter le format de l’image",
    "error.cannot_shrink": "Impossible de réduire l’image à 999 Ko",
    "error.encoded_too_large": "L’image encodée dépasse la cible de 999 Ko",
    "error.jpeg_eoi": "Marqueur de fin JPEG introuvable",
    "error.not_png": "Ce n’est pas un fichier PNG",
    "error.png_iend": "Bloc IEND PNG introuvable",
    "error.gif_trailer": "Fin de fichier GIF introuvable",
    "error.not_webp": "Ce n’est pas un fichier WebP",
    "error.unsupported_encode_format": "Format d’image non pris en charge : {fmt}",
}

_IT: dict[str, str] = {
    "window.title": "Immagine GitHub a 999 KB",
    "header.title": "Immagine GitHub a 999 KB",
    "header.subtitle": (
        "Scegli un’immagine. Proporzioni e formato restano invariati.\n"
        "Il file salvato è esattamente 999 KB (999.000 byte),\n"
        "sotto il limite di 1 MB di GitHub (1.000.000 byte)."
    ),
    "language.label": "Lingua",
    "button.choose": "Scegli immagine…",
    "button.save": "Salva come 999 KB…",
    "preview.empty": "Nessuna immagine selezionata",
    "info.choose_prompt": "Seleziona un’immagine.",
    "dialog.images": "Immagini",
    "dialog.jpeg": "JPEG",
    "dialog.png": "PNG",
    "dialog.gif": "GIF",
    "dialog.webp": "WebP",
    "dialog.all_files": "Tutti i file",
    "error.unsupported_format_title": "Formato non supportato",
    "error.unsupported_format_body": "Scegli JPEG, PNG, GIF o WebP.",
    "error.load_failed_title": "Impossibile caricare l’immagine",
    "info.selected": (
        "File: {name}\n"
        "Formato: {fmt}  |  Dimensioni: {width} × {height} px\n"
        "Dimensione attuale: {bytes:,} byte ({kb:.1f} KB)\n"
        "Dimensione obiettivo: {target:,} byte (999 KB, sotto 1.000.000 byte)"
    ),
    "status.ready": "Pronto per il salvataggio.",
    "progress.resizing": "Adeguamento del file…",
    "success.saved": "Salvato: {name}",
    "success.result": "Risultato: {size:,} byte (999 KB)",
    "success.dimensions": "Dimensioni: {width} × {height} px",
    "success.format": "Formato: {fmt}",
    "success.scaled": "La risoluzione è stata ridotta mantenendo le proporzioni.",
    "success.padded": "Il file originale era inferiore a 999 KB ed è stato solo riempito.",
    "info.saved_file": (
        "File salvato: {path}\nDimensione: {size:,} byte\nDimensioni: {width} × {height} px"
    ),
    "dialog.done_title": "Completato",
    "dialog.done_body": "Il file è esattamente di {size:,} byte.",
    "status.error": "Errore: {message}",
    "error.resize_failed_title": "Adeguamento non riuscito",
    "error.cannot_fit_title": "Impossibile portare l’immagine a 999 KB",
    "progress.loading": "Caricamento dell’immagine…",
    "progress.padding": "Il file è più piccolo di 999 KB — solo riempimento…",
    "progress.adjusting": "Adeguamento di dimensione e qualità…",
    "progress.scaling": "Riduzione della risoluzione mantenendo le proporzioni…",
    "error.target_over_limit": "L’obiettivo deve restare sotto il limite di 1 MB di GitHub (1.000.000 byte)",
    "error.unsupported_suffix": "Formato immagine non supportato: {suffix}",
    "error.cannot_pad": "Impossibile riempire l’immagine codificata a esattamente 999 KB",
    "error.detect_format": "Impossibile rilevare il formato dell’immagine",
    "error.cannot_shrink": "Impossibile ridurre l’immagine a 999 KB",
    "error.encoded_too_large": "L’immagine codificata supera l’obiettivo di 999 KB",
    "error.jpeg_eoi": "Marcatore finale JPEG non trovato",
    "error.not_png": "Non è un file PNG",
    "error.png_iend": "Chunk IEND PNG non trovato",
    "error.gif_trailer": "Trailer GIF non trovato",
    "error.not_webp": "Non è un file WebP",
    "error.unsupported_encode_format": "Formato immagine non supportato: {fmt}",
}

_PT_BR: dict[str, str] = {
    "window.title": "Imagem do GitHub em 999 KB",
    "header.title": "Imagem do GitHub em 999 KB",
    "header.subtitle": (
        "Escolha uma imagem. A proporção e o formato são mantidos.\n"
        "O arquivo salvo tem exatamente 999 KB (999.000 bytes),\n"
        "abaixo do limite de 1 MB do GitHub (1.000.000 bytes)."
    ),
    "language.label": "Idioma",
    "button.choose": "Escolher imagem…",
    "button.save": "Salvar como 999 KB…",
    "preview.empty": "Nenhuma imagem selecionada ainda",
    "info.choose_prompt": "Escolha uma imagem.",
    "dialog.images": "Imagens",
    "dialog.jpeg": "JPEG",
    "dialog.png": "PNG",
    "dialog.gif": "GIF",
    "dialog.webp": "WebP",
    "dialog.all_files": "Todos os arquivos",
    "error.unsupported_format_title": "Formato não suportado",
    "error.unsupported_format_body": "Escolha JPEG, PNG, GIF ou WebP.",
    "error.load_failed_title": "Não foi possível carregar a imagem",
    "info.selected": (
        "Arquivo: {name}\n"
        "Formato: {fmt}  |  Tamanho: {width} × {height} px\n"
        "Tamanho atual: {bytes:,} bytes ({kb:.1f} KB)\n"
        "Tamanho alvo: {target:,} bytes (999 KB, abaixo de 1.000.000 bytes)"
    ),
    "status.ready": "Pronto para salvar.",
    "progress.resizing": "Ajustando o arquivo…",
    "success.saved": "Salvo: {name}",
    "success.result": "Resultado: {size:,} bytes (999 KB)",
    "success.dimensions": "Dimensões: {width} × {height} px",
    "success.format": "Formato: {fmt}",
    "success.scaled": "A resolução foi reduzida mantendo a proporção.",
    "success.padded": "O arquivo original era menor que 999 KB e foi apenas preenchido.",
    "info.saved_file": (
        "Arquivo salvo: {path}\nTamanho: {size:,} bytes\nDimensões: {width} × {height} px"
    ),
    "dialog.done_title": "Concluído",
    "dialog.done_body": "O arquivo tem exatamente {size:,} bytes.",
    "status.error": "Erro: {message}",
    "error.resize_failed_title": "Falha no ajuste",
    "error.cannot_fit_title": "Não foi possível ajustar a imagem para 999 KB",
    "progress.loading": "Carregando imagem…",
    "progress.padding": "O arquivo é menor que 999 KB — apenas preenchimento…",
    "progress.adjusting": "Ajustando tamanho e qualidade…",
    "progress.scaling": "Reduzindo a resolução e mantendo a proporção…",
    "error.target_over_limit": "O alvo deve permanecer abaixo do limite de 1 MB do GitHub (1.000.000 bytes)",
    "error.unsupported_suffix": "Formato de imagem não suportado: {suffix}",
    "error.cannot_pad": "Não foi possível preencher a imagem codificada para exatamente 999 KB",
    "error.detect_format": "Não foi possível detectar o formato da imagem",
    "error.cannot_shrink": "Não foi possível reduzir a imagem para 999 KB",
    "error.encoded_too_large": "A imagem codificada é maior que o alvo de 999 KB",
    "error.jpeg_eoi": "Marcador final JPEG não encontrado",
    "error.not_png": "Não é um arquivo PNG",
    "error.png_iend": "Chunk IEND PNG não encontrado",
    "error.gif_trailer": "Trailer GIF não encontrado",
    "error.not_webp": "Não é um arquivo WebP",
    "error.unsupported_encode_format": "Formato de imagem não suportado: {fmt}",
}

_JA: dict[str, str] = {
    "window.title": "GitHub 画像を 999 KB に",
    "header.title": "GitHub 画像を 999 KB に",
    "header.subtitle": (
        "画像を選びます。縦横比と形式はそのままです。\n"
        "保存ファイルは正確に 999 KB（999,000 バイト）で、\n"
        "GitHub の 1 MB 制限（1,000,000 バイト）未満です。"
    ),
    "language.label": "言語",
    "button.choose": "画像を選択…",
    "button.save": "999 KB で保存…",
    "preview.empty": "まだ画像が選ばれていません",
    "info.choose_prompt": "画像を選択してください。",
    "dialog.images": "画像",
    "dialog.jpeg": "JPEG",
    "dialog.png": "PNG",
    "dialog.gif": "GIF",
    "dialog.webp": "WebP",
    "dialog.all_files": "すべてのファイル",
    "error.unsupported_format_title": "未対応の形式",
    "error.unsupported_format_body": "JPEG、PNG、GIF、または WebP を選んでください。",
    "error.load_failed_title": "画像を読み込めませんでした",
    "info.selected": (
        "ファイル: {name}\n"
        "形式: {fmt}  |  サイズ: {width} × {height} px\n"
        "現在の容量: {bytes:,} バイト ({kb:.1f} KB)\n"
        "目標容量: {target:,} バイト（999 KB、1,000,000 バイト未満）"
    ),
    "status.ready": "保存できます。",
    "progress.resizing": "ファイルを調整しています…",
    "success.saved": "保存しました: {name}",
    "success.result": "結果: {size:,} バイト（999 KB）",
    "success.dimensions": "サイズ: {width} × {height} px",
    "success.format": "形式: {fmt}",
    "success.scaled": "縦横比を保ったまま解像度を下げました。",
    "success.padded": "元のファイルは 999 KB 未満だったため、埋め込みのみ行いました。",
    "info.saved_file": (
        "保存したファイル: {path}\n容量: {size:,} バイト\nサイズ: {width} × {height} px"
    ),
    "dialog.done_title": "完了",
    "dialog.done_body": "ファイルは正確に {size:,} バイトです。",
    "status.error": "エラー: {message}",
    "error.resize_failed_title": "調整に失敗しました",
    "error.cannot_fit_title": "画像を 999 KB に合わせられませんでした",
    "progress.loading": "画像を読み込んでいます…",
    "progress.padding": "ファイルは 999 KB 未満です — 埋め込みのみ…",
    "progress.adjusting": "サイズと品質を調整しています…",
    "progress.scaling": "縦横比を保ったまま解像度を下げています…",
    "error.target_over_limit": "目標は GitHub の 1 MB 制限（1,000,000 バイト）未満である必要があります",
    "error.unsupported_suffix": "未対応の画像形式: {suffix}",
    "error.cannot_pad": "エンコード済み画像を正確に 999 KB に埋め込めませんでした",
    "error.detect_format": "画像形式を検出できませんでした",
    "error.cannot_shrink": "画像を 999 KB まで縮小できませんでした",
    "error.encoded_too_large": "エンコード済み画像が 999 KB の目標より大きいです",
    "error.jpeg_eoi": "JPEG 終了マーカーが見つかりません",
    "error.not_png": "PNG ファイルではありません",
    "error.png_iend": "PNG の IEND チャンクが見つかりません",
    "error.gif_trailer": "GIF トレイラーが見つかりません",
    "error.not_webp": "WebP ファイルではありません",
    "error.unsupported_encode_format": "未対応の画像形式: {fmt}",
}

_KO: dict[str, str] = {
    "window.title": "GitHub 이미지를 999 KB로",
    "header.title": "GitHub 이미지를 999 KB로",
    "header.subtitle": (
        "이미지를 선택하세요. 가로세로 비율과 형식은 유지됩니다.\n"
        "저장된 파일은 정확히 999 KB(999,000바이트)이며,\n"
        "GitHub의 1 MB 제한(1,000,000바이트)보다 작습니다."
    ),
    "language.label": "언어",
    "button.choose": "이미지 선택…",
    "button.save": "999 KB로 저장…",
    "preview.empty": "아직 선택한 이미지가 없습니다",
    "info.choose_prompt": "이미지를 선택하세요.",
    "dialog.images": "이미지",
    "dialog.jpeg": "JPEG",
    "dialog.png": "PNG",
    "dialog.gif": "GIF",
    "dialog.webp": "WebP",
    "dialog.all_files": "모든 파일",
    "error.unsupported_format_title": "지원하지 않는 형식",
    "error.unsupported_format_body": "JPEG, PNG, GIF 또는 WebP를 선택하세요.",
    "error.load_failed_title": "이미지를 불러올 수 없습니다",
    "info.selected": (
        "파일: {name}\n"
        "형식: {fmt}  |  크기: {width} × {height} px\n"
        "현재 용량: {bytes:,}바이트 ({kb:.1f} KB)\n"
        "목표 용량: {target:,}바이트 (999 KB, 1,000,000바이트 미만)"
    ),
    "status.ready": "저장할 준비가 되었습니다.",
    "progress.resizing": "파일을 맞추는 중…",
    "success.saved": "저장됨: {name}",
    "success.result": "결과: {size:,}바이트 (999 KB)",
    "success.dimensions": "크기: {width} × {height} px",
    "success.format": "형식: {fmt}",
    "success.scaled": "가로세로 비율을 유지한 채 해상도를 줄였습니다.",
    "success.padded": "원본 파일이 999 KB보다 작아서 패딩만 적용했습니다.",
    "info.saved_file": (
        "저장된 파일: {path}\n용량: {size:,}바이트\n크기: {width} × {height} px"
    ),
    "dialog.done_title": "완료",
    "dialog.done_body": "파일은 정확히 {size:,}바이트입니다.",
    "status.error": "오류: {message}",
    "error.resize_failed_title": "조정 실패",
    "error.cannot_fit_title": "이미지를 999 KB로 맞출 수 없습니다",
    "progress.loading": "이미지를 불러오는 중…",
    "progress.padding": "파일이 999 KB보다 작습니다 — 패딩만 적용…",
    "progress.adjusting": "크기와 품질을 조정하는 중…",
    "progress.scaling": "가로세로 비율을 유지한 채 해상도를 줄이는 중…",
    "error.target_over_limit": "목표는 GitHub의 1 MB 제한(1,000,000바이트)보다 작아야 합니다",
    "error.unsupported_suffix": "지원하지 않는 이미지 형식: {suffix}",
    "error.cannot_pad": "인코딩된 이미지를 정확히 999 KB로 채울 수 없습니다",
    "error.detect_format": "이미지 형식을 감지할 수 없습니다",
    "error.cannot_shrink": "이미지를 999 KB까지 줄일 수 없습니다",
    "error.encoded_too_large": "인코딩된 이미지가 999 KB 목표보다 큽니다",
    "error.jpeg_eoi": "JPEG 종료 마커를 찾을 수 없습니다",
    "error.not_png": "PNG 파일이 아닙니다",
    "error.png_iend": "PNG IEND 청크를 찾을 수 없습니다",
    "error.gif_trailer": "GIF 트레일러를 찾을 수 없습니다",
    "error.not_webp": "WebP 파일이 아닙니다",
    "error.unsupported_encode_format": "지원하지 않는 이미지 형식: {fmt}",
}

_ZH_CN: dict[str, str] = {
    "window.title": "将 GitHub 图片调整为 999 KB",
    "header.title": "将 GitHub 图片调整为 999 KB",
    "header.subtitle": (
        "选择一张图片。宽高比和格式保持不变。\n"
        "保存的文件正好是 999 KB（999,000 字节），\n"
        "低于 GitHub 的 1 MB 限制（1,000,000 字节）。"
    ),
    "language.label": "语言",
    "button.choose": "选择图片…",
    "button.save": "保存为 999 KB…",
    "preview.empty": "尚未选择图片",
    "info.choose_prompt": "请选择一张图片。",
    "dialog.images": "图片",
    "dialog.jpeg": "JPEG",
    "dialog.png": "PNG",
    "dialog.gif": "GIF",
    "dialog.webp": "WebP",
    "dialog.all_files": "所有文件",
    "error.unsupported_format_title": "不支持的格式",
    "error.unsupported_format_body": "请选择 JPEG、PNG、GIF 或 WebP。",
    "error.load_failed_title": "无法加载图片",
    "info.selected": (
        "文件：{name}\n"
        "格式：{fmt}  |  尺寸：{width} × {height} px\n"
        "当前大小：{bytes:,} 字节（{kb:.1f} KB）\n"
        "目标大小：{target:,} 字节（999 KB，低于 1,000,000 字节）"
    ),
    "status.ready": "可以保存。",
    "progress.resizing": "正在调整文件…",
    "success.saved": "已保存：{name}",
    "success.result": "结果：{size:,} 字节（999 KB）",
    "success.dimensions": "尺寸：{width} × {height} px",
    "success.format": "格式：{fmt}",
    "success.scaled": "已在保持宽高比的情况下降低分辨率。",
    "success.padded": "原始文件小于 999 KB，仅进行了填充。",
    "info.saved_file": (
        "已保存文件：{path}\n大小：{size:,} 字节\n尺寸：{width} × {height} px"
    ),
    "dialog.done_title": "完成",
    "dialog.done_body": "该文件正好是 {size:,} 字节。",
    "status.error": "错误：{message}",
    "error.resize_failed_title": "调整失败",
    "error.cannot_fit_title": "无法将图片调整为 999 KB",
    "progress.loading": "正在加载图片…",
    "progress.padding": "文件小于 999 KB — 仅填充…",
    "progress.adjusting": "正在调整大小和质量…",
    "progress.scaling": "正在保持宽高比并降低分辨率…",
    "error.target_over_limit": "目标必须低于 GitHub 的 1 MB 限制（1,000,000 字节）",
    "error.unsupported_suffix": "不支持的图片格式：{suffix}",
    "error.cannot_pad": "无法将编码后的图片填充到正好 999 KB",
    "error.detect_format": "无法检测图片格式",
    "error.cannot_shrink": "无法将图片缩小到 999 KB",
    "error.encoded_too_large": "编码后的图片大于 999 KB 目标",
    "error.jpeg_eoi": "未找到 JPEG 结束标记",
    "error.not_png": "不是 PNG 文件",
    "error.png_iend": "未找到 PNG IEND 数据块",
    "error.gif_trailer": "未找到 GIF 结束标记",
    "error.not_webp": "不是 WebP 文件",
    "error.unsupported_encode_format": "不支持的图片格式：{fmt}",
}

CATALOGS: dict[str, dict[str, str]] = {
    "en": _EN,
    "es": _ES,
    "de": _DE,
    "fr": _FR,
    "it": _IT,
    "pt-BR": _PT_BR,
    "ja": _JA,
    "ko": _KO,
    "zh-CN": _ZH_CN,
}


def normalize_language(value: str | None) -> str | None:
    """Return a supported language code, or None if the tag does not match."""
    if not value:
        return None
    raw = value.strip().replace("_", "-")
    if not raw:
        return None
    raw = raw.split(".", maxsplit=1)[0].split("@", maxsplit=1)[0]
    lower = raw.lower()
    if not lower:
        return None

    if lower.startswith("zh"):
        if any(token in lower for token in ("hant", "zh-tw", "zh-hk", "zh-mo")):
            return None
        if (
            lower == "zh"
            or lower.startswith("zh-cn")
            or lower.startswith("zh-sg")
            or "hans" in lower
        ):
            return "zh-CN"
        return None

    if lower.startswith("pt"):
        if lower.startswith("pt-br"):
            return "pt-BR"
        return None

    prefix = lower.split("-", maxsplit=1)[0]
    mapping = {
        "en": "en",
        "es": "es",
        "de": "de",
        "fr": "fr",
        "it": "it",
        "ja": "ja",
        "ko": "ko",
    }
    return mapping.get(prefix)


def switcher_codes() -> tuple[str, ...]:
    return SWITCHER_CODES


def language_from_switcher(code: str) -> str | None:
    return CODE_BY_SWITCHER.get(code)


def switcher_from_language(language: str) -> str:
    return SWITCHER_BY_CODE.get(language, SWITCHER_BY_CODE[DEFAULT_LANGUAGE])


def config_dir(
    environ: dict[str, str] | None = None, *, home: Path | None = None
) -> Path:
    env = environ if environ is not None else os.environ
    home_path = home if home is not None else Path.home()
    if sys.platform == "win32":
        base = env.get("APPDATA")
        return Path(base) / APP_DIR_NAME if base else home_path / APP_DIR_NAME
    if sys.platform == "darwin":
        return home_path / "Library" / "Application Support" / APP_DIR_NAME
    xdg = env.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg) / APP_DIR_NAME
    return home_path / ".config" / APP_DIR_NAME


def settings_path(
    environ: dict[str, str] | None = None, *, home: Path | None = None
) -> Path:
    return config_dir(environ, home=home) / SETTINGS_FILENAME


def load_saved_language(
    path: Path | None = None,
    environ: dict[str, str] | None = None,
    *,
    home: Path | None = None,
) -> str | None:
    target = path if path is not None else settings_path(environ, home=home)
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    saved = payload.get("language")
    if not isinstance(saved, str):
        return None
    return saved if saved in SUPPORTED_LANGUAGES else normalize_language(saved)


def save_language(
    language: str,
    path: Path | None = None,
    environ: dict[str, str] | None = None,
    *,
    home: Path | None = None,
) -> None:
    if language not in SUPPORTED_LANGUAGES:
        language = DEFAULT_LANGUAGE
    target = path if path is not None else settings_path(environ, home=home)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps({"language": language}, indent=2) + "\n", encoding="utf-8"
    )


def detect_os_language(
    tags: list[str] | None = None,
    environ: dict[str, str] | None = None,
) -> str | None:
    """Return the first supported language matching OS locale tags."""
    for tag in tags if tags is not None else _os_locale_tags(environ):
        matched = normalize_language(tag)
        if matched is not None:
            return matched
    return None


def resolve_language(
    saved: str | None = None,
    os_language: str | None = None,
) -> str:
    if saved in SUPPORTED_LANGUAGES:
        return saved
    if os_language in SUPPORTED_LANGUAGES:
        return os_language
    return DEFAULT_LANGUAGE


def translate(language: str, key: str, **params: object) -> str:
    catalog = CATALOGS.get(language, CATALOGS[DEFAULT_LANGUAGE])
    template = catalog.get(key) or CATALOGS[DEFAULT_LANGUAGE].get(key, key)
    if params:
        return template.format(**params)
    return template


def _os_locale_tags(environ: dict[str, str] | None = None) -> list[str]:
    env = environ if environ is not None else os.environ
    tags: list[str] = []
    tags.extend(_windows_ui_language_tags())
    for getter in (locale.getlocale, locale.getdefaultlocale):
        try:
            value = getter()[0]
        except (TypeError, ValueError, locale.Error):
            value = None
        if value:
            tags.append(value)
    for name in ("LC_ALL", "LC_MESSAGES", "LANG"):
        value = env.get(name)
        if value:
            tags.append(value)
    return tags


def _windows_ui_language_tags() -> list[str]:
    if sys.platform != "win32":
        return []
    try:
        import ctypes

        lcid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
        name = locale.windows_locale.get(int(lcid))
    except (AttributeError, OSError, TypeError, ValueError):
        return []
    return [name] if name else []
