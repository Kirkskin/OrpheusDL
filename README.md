<!-- PROJECT INTRO -->

<img src='https://svgshare.com/i/__W.svg' title='Orfi_temporary' height="150">

OrpheusDL
=========

AI-assisted modular music archival suite

[Report Bug](https://github.com/OrfiTeam/OrpheusDL/issues)
·
[Request Feature](https://github.com/OrfiTeam/OrpheusDL/issues)


## Highlights

- Central **Orpheus Brain** collects telemetry from networking, login, delivery,
  and CLI layers, providing actionable hints in real time.
- Unified **Network Manager** with circuit breaker support, DNS diagnostics,
  and optional offline simulation for testing.
- **Service Registry & Session Manager** track module capabilities, credentials,
  and pluggable login strategies (ARL, token, username/password).
- **Delivery Pipeline** emits structured job events and is ready for queued or
  parallel downloads.
- **Interactive CLI Watchdog** exposes an AI-assisted menu (`--menu`) for health
  checks, configuration introspection, and guided flows.
- Extension SDK with shipping examples: `assistant` for guidance and `logger`
  for structured event logs.


## Table of content

- [Highlights](#highlights)
- [About OrpheusDL](#about-orpheusdl)
- [Getting Started](#getting-started)
    - [Prerequisites](#prerequisites)
    - [Installation](#installation)
- [Usage](#usage)
    - [Interactive CLI](#interactive-cli)
    - [Offline mode and diagnostics](#offline-mode-and-diagnostics)
- [Configuration](#configuration)
    - [Global/Formatting](#globalformatting)
        - [Format variables](#format-variables)
- [Architecture & Roadmap](#architecture--roadmap)
- [Development](#development)
- [Contact](#contact)
- [Acknowledgements](#acknowledgements)



<!-- ABOUT ORPHEUS -->
## About OrpheusDL

OrpheusDL is a modular music archival tool written in Python which allows archiving from multiple different services.


<!-- GETTING STARTED -->
## Getting Started

Follow these steps to get a local copy of Orpheus up and running:

### Prerequisites

* Python 3.7+ (due to the requirement of dataclasses), though Python 3.9 is highly recommended

### Installation

1. Clone the repo
    ```shell
    git clone https://github.com/OrfiTeam/OrpheusDL.git && cd OrpheusDL
    ```
2. Install all requirements
   ```shell
   pip install -r requirements.txt
   ```
3. Duplicate the environment template and populate credentials/tokens:
   ```shell
   cp .env.template .env
   # edit .env with your service secrets
   ```
4. Run the program at least once, or use this command to create the settings file
   ```shell
   python3 orpheus.py settings refresh
   ```
5. Adjust defaults in `config/settings.json` if needed (download path, quality).

<!-- USAGE EXAMPLES -->
## Usage

Just call `orpheus.py` with any link you want to archive, for example Qobuz:
```shell
python3 orpheus.py https://open.qobuz.com/album/c9wsrrjh49ftb
```

Alternatively do a search (luckysearch to automatically select the first option):
```shell
python3 orpheus.py search qobuz track darkside alan walker
```

Or if you have the ID of what you want to download, use:
```shell
python3 orpheus.py download qobuz track 52151405
```

### Interactive CLI

Prefer a guided experience? Launch the AI-assisted menu:

```shell
python3 orpheus.py --menu
```

The menu currently offers module health checks, configuration summaries, and
service capability listings. Extensions can register new actions without
changing core code.

### Offline mode and diagnostics

When upstream services are unreachable (VPNs, DNS blocking), you can simulate
behaviour without hitting the network:

```shell
python3 orpheus.py config offline on
```

Disable it again with `python3 orpheus.py config offline off`. After each
command the CLI watchdog prints AI hints, calling out DNS, SSL, or auth issues.

<!-- CONFIGURATION -->
## Configuration

You can customize every module from Orpheus individually and also set general/global settings which are active in every
loaded module. You'll find the configuration file here: `config/settings.json`

### Global/General
```json5
{
    "download_path": "./downloads/",
    "download_quality": "hifi",
    "search_limit": 10
}
```

`download_path`: Set the absolute or relative output path with `/` as the delimiter

`download_quality`: Choose one of the following settings:
* "hifi": FLAC higher than 44.1/16 if available
* "lossless": FLAC with 44.1/16 if available
* "high": lossy codecs such as MP3, AAC, ... in a higher bitrate
* "medium": lossy codecs such as MP3, AAC, ... in a medium bitrate
* "low": lossy codecs such as MP3, AAC, ... in a lower bitrate

**NOTE: The `download_quality` really depends on the used modules, so check out the modules README.md**

`search_limit`: How many search results are shown


### Global/Formatting:

```json5
{
    "album_format": "{name}{explicit}",
    "playlist_format": "{name}{explicit}",
    "track_filename_format": "{track_number}. {name}",
    "single_full_path_format": "{name}",
    "enable_zfill": true,
    "force_album_format": false
}
```

`track_filename_format`: How tracks are formatted in albums and playlists. The relevant extension is appended to the end.

`album_format`, `playlist_format`, `artist_format`: Base directories for their respective formats - tracks and cover
art are stored here. May have slashes in it, for instance {artist}/{album}.

`single_full_path_format`: How singles are handled, which is separate to how the above work.
Instead, this has both the folder's name and the track's name.

`enable_zfill`: Enables zero padding for `track_number`, `total_tracks`, `disc_number`, `total_discs` if the
corresponding number has more than 2 digits

`force_album_format`: Forces the `album_format` for tracks instead of the `single_full_path_format` and also
uses `album_format` in the `playlist_format` folder 


#### Format variables

`track_filename_format` variables are `{name}`, `{album}`, `{album_artist}`, `{album_id}`, `{track_number}`,
`{total_tracks}`, `{disc_number}`, `{total_discs}`, `{release_date}`, `{release_year}`, `{artist_id}`, `{isrc}`,
`{upc}`, `{explicit}`, `{copyright}`, `{codec}`, `{sample_rate}`, `{bit_depth}`.

`album_format` variables are `{name}`, `{id}`, `{artist}`, `{artist_id}`, `{release_year}`, `{upc}`, `{explicit}`,
`{quality}`, `{artist_initials}`.

`playlist_format` variables are `{name}`, `{creator}`, `{tracks}`, `{release_year}`, `{explicit}`, `{creator_id}`

* `{quality}` will add
    ```
     [Dolby Atmos]
     [96kHz 24bit]
     [M]
    ```
 to the corresponding path (depending on the module)
* `{explicit}` will add
    ```
     [E]
    ```
  to the corresponding path

### Global/Covers

```json5
{
    "embed_cover": true,
    "main_compression": "high",
    "main_resolution": 1400,
    "save_external": false,
    "external_format": "png",
    "external_compression": "low",
    "external_resolution": 3000,
    "save_animated_cover": true
}
```

| Option               | Info                                                                                     |
|----------------------|------------------------------------------------------------------------------------------|
| embed_cover          | Enable it to embed the album cover inside every track                                    |
| main_compression     | Compression of the main cover                                                            |
| main_resolution      | Resolution (in pixels) of the cover of the module used                                   |
| save_external        | Enable it to save the cover from a third party cover module                              |
| external_format      | Format of the third party cover, supported values: `jpg`, `png`, `webp`                  |
| external_compression | Compression of the third party cover, supported values: `low`, `high`                    |
| external_resolution  | Resolution (in pixels) of the third party cover                                          |
| save_animated_cover  | Enable saving the animated cover when supported from the module (often in MPEG-4 format) |

### Global/Codecs

```json5
{
    "proprietary_codecs": false,
    "spatial_codecs": true
}
```

`proprietary_codecs`: Enable it to allow `MQA`, `E-AC-3 JOC` or `AC-4 IMS`

`spatial_codecs`: Enable it to allow `MPEG-H 3D`, `E-AC-3 JOC` or `AC-4 IMS`

**Note: `spatial_codecs` has priority over `proprietary_codecs` when deciding if a codec is enabled**

### Global/Module_defaults

```json5
{
    "lyrics": "default",
    "covers": "default",
    "credits": "default"
}
```

Change `default` to the module name under `/modules` in order to retrieve `lyrics`, `covers` or `credits` from the
selected module

### Global/Lyrics
```json5
{
    "embed_lyrics": true,
    "embed_synced_lyrics": false,
    "save_synced_lyrics": true
}
```

| Option              | Info                                                                                                                                                                |
|---------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| embed_lyrics        | Embeds the (unsynced) lyrics inside every track                                                                                                                     |
| embed_synced_lyrics | Embeds the synced lyrics inside every track (needs `embed_lyrics` to be enabled) (required for [Roon](https://community.roonlabs.com/t/1-7-lyrics-tag-guide/85182)) |
| save_synced_lyrics  | Saves the synced lyrics inside a  `.lrc` file in the same directory as the track with the same `track_format` variables                                             |

## Architecture & Roadmap

The legacy roadmap has been superseded by an AI-centric blueprint. See
[`docs/architecture_overview.md`](docs/architecture_overview.md) for details on
the Orpheus Brain, service registry, login manager, network fabric, delivery
pipeline, CLI, and extension ecosystem. That document is the authoritative
guide for new development.

## Development

Run the automated tests before submitting changes:

```shell
/tmp/orpheus_venv/bin/python -m unittest tests.test_core tests.test_network tests.test_services tests.test_integration
```

When adding modules or extensions, implement the contracts defined in
`orpheus/modules/base.py` and `orpheus/extensions/sdk.py`, emitting telemetry so
the brain can keep users informed.

<!-- Contact -->
## Contact

OrfiDev (Project Lead) - [@OrfiDev](https://github.com/OrfiTeam)

Dniel97 (Current Lead Developer) - [@Dniel97](https://github.com/Dniel97)

Project Link: [Orpheus Public GitHub Repository](https://github.com/OrfiTeam/OrpheusDL)



<!-- ACKNOWLEDGEMENTS -->
## Acknowledgements
* Chimera by Aesir - the inspiration to the project
* [Icon modified from a freepik image](https://www.freepik.com/)
