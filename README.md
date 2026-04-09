# Angels and Demons

Game nho bang `pygame` theo phong cach party board game: mo o, an effect, lat keo tran va dua diem voi nhau.

## Tinh nang hien tai

- 8 hieu ung mac dinh: `May man`, `Trung so`, `Keo bua bao`, `Sung`, `Thien than`, `Ac quy`, `Nhan doi`, `Chia doi`
- Effect dac biet chi mo trong `custom`: `La chan`, `Doi menh`, `Dao chieu`, `Tien tri`
- Nhac nen, SFX, icon va effect art da gan san
- `Solo vs Bot`, `Challenge`, `Best of 3`
- `Settings`, `History`, `Stats`, `Achievements`
- Tooltip hover va `So tay hieu ung`

## Cai dat

```powershell
python -m pip install -r requirements.txt
```

## Chay game

```powershell
python angels_and_demons_game\Angels_and_Demons.py
```

Neu muon build exe:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\build_release.ps1
```

## Dieu khien nhanh

- `Enter`: xac nhan / bat dau
- `H`: mo huong dan nhanh trong tran
- `B`: mo `So tay hieu ung`
- `T`: bat / tat tooltip nhanh
- `M`: mute nhanh nhac va SFX
- `1` / `2`: chon ket qua cho `Keo bua bao`
- Chuot trai: mo o, chon nguoi choi, bam nut UI

## Che do choi

- `Classic`: mot van thong thuong
- `Solo vs Bot`: 1 nguoi dau 1 bot AI
- `Challenge`: bo preset thu thach co san
- Challenge hien co: `Chaos Trial`, `Halo Harvest`, `Devil's Gauntlet`, `Mind Maze`
- `Best of 3`: can 2 van thang de vo dich series

## Thu muc quan trong

- [angels_and_demons_game/ui/menu.py](d:/GitHub/Angels-and-Demons/angels_and_demons_game/ui/menu.py)
- [angels_and_demons_game/ui/game_screen.py](d:/GitHub/Angels-and-Demons/angels_and_demons_game/ui/game_screen.py)
- [angels_and_demons_game/ui/effect_book_screen.py](d:/GitHub/Angels-and-Demons/angels_and_demons_game/ui/effect_book_screen.py)
- [angels_and_demons_game/ui/custom_setup.py](d:/GitHub/Angels-and-Demons/angels_and_demons_game/ui/custom_setup.py)
- [angels_and_demons_game/ui/custom_mode_setup.py](d:/GitHub/Angels-and-Demons/angels_and_demons_game/ui/custom_mode_setup.py)

## Asset va build helper

- Tao lai brand asset: `python tools\generate_brand_assets.py`
- Tao lai SFX: `python tools\generate_sound_fx.py`
- Build release: `tools\build_release.ps1`
- Don artefact build/cache: `tools\clean_release_artifacts.ps1`
