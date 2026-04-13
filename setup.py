from setuptools import setup

setup(
    name="ufka_kanat_vr",
    options={
        'build_apps': {
            'gui_apps': {'ufka_kanat': 'neonvfghjkliü.py'}, # Dosya adın neyse onu yaz
            'platforms': ['wasm_runtime'], # İşte bu sihirli kelime!
        }
    }
)