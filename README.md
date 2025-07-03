# EverSD Game Manager

A simple desktop application for managing game entries on an EverSD flash cart.

## Motivation

The official Evercade management software, EverLoader, is Windows-only. This project was created to provide a native, open-source alternative for Linux users.

## Features

*   **Game Library Management:** List, add, edit, and delete game entries.
*   **Metadata Editing:** Modify game titles, descriptions, genres, and more.
*   **Image Management:** Add and replace box art and banner images for your games.
*   **Online Search:** Find box art and banners for your games using an online search.
*   **Vimm.net Integration:** Fetch game metadata directly from a Vimm.net URL.
*   **SD Card Detection:** Automatically detects mounted SD cards on Arch Linux.

## Limitations

*   This application has only been tested on a personal Arch Linux installation. The automatic SD card detection is specific to this setup (`/run/media/[user]`). Other operating systems or configurations will require users to browse for their EverSD path manually.

## Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/your-username/eversd_manager.git
    ```
2.  Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Run the application:
    ```bash
    python3 main.py
    ```

## Usage

1.  Select your EverSD path using the dropdown menu or the "Browse" button.
2.  The application will automatically scan for existing games and display them in the list.
3.  Click on a game to view its details.
4.  Use the "Add New Game," "Edit Selected Game," and "Delete Selected Game" buttons to manage your library.
