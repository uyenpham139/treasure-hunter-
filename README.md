# TREASURE HUNTER

## 📝 Description

This is a 2D side-scrolling platformer built with Pygame. It features a playable character, multiple enemy types, collectibles, a boss battle, and a complete, built-in level editor.

## 📌 Features

- Level Editor: A fully functional, in-game level editor. Create, save, and play your own levels.

- Game States: A robust state machine manages the Main Menu, Level Editor, main game (Level), and End Screen.

- Player Mechanics: Run, jump, attack and air attack (jump + attack). Includes a health system, invincibility frames, and an inventory.

### Diverse Enemies:

- Spikes: Simple static hazards.

- Tooth: A walking, patrolling enemy that chases the player on sight.

- Shell: A stationary turret enemy that shoots pearl projectiles.

- Crabby (Boss): A boss enemy with a large health bar, dedicated boss area, and multiple AI states (idle, run, attack, return to origin).

### Items & Inventory:

- Collect three types of coins (gold, silver, diamond).

- Pick up items: health potions, keys, and checkpoint maps.

- Toggle a simple 3-slot inventory to use items.

- Progression: The game's objective is to defeat the boss (Crabby), which spawns a locked treasure chest. You must then find the key and open the chest to win.

### Menus:

- Main Menu: Start a new game, enter the editor, or quit.

- Options Menu: A pausable in-game menu (and main menu screen) to adjust music and SFX volume.

### Dynamic World:

- A scrolling `CameraGroup` follows the player.

- A dynamic sky with procedurally spawned, moving clouds.

- Animated water, coins, and characters.

## 🛠️ Installation & Requirements

Python 3.x: Ensure you have Python 3 installed on your system.

Pygame: Install the Pygame library using pip.

```bash
pip install pygame
```

## 💻 How to Run

**IMPORTANT**: The game requires a level file (saved_level_grid.json) to run. You must use the editor to create and save a level first.

1. Run the game:
```bash
python main.py
```

2. Enter the Editor: From the main menu, click the "Editor" button (top right).

3. Create a Level:

    - Use the mouse and the right-hand menu to select tiles.

    - Click to place tiles on the grid.

    - You must place a 'player' tile (from the 'object' menu) for the level to work.

    - Place some 'terrain' tiles for the player to stand on.

4. Save the Level: Press the ENTER key while in the editor to save your level.

5. Play: Press ESCAPE to return to the main menu. Click "New Game" to play the level you just created.

## Controls

### In-Game (Level)

- Left/Right Arrow Keys: Move character

- Spacebar: Jump

- F Key: Attack (or Interact with items/chests)

- Z Key: Toggle Inventory

- ESCAPE: Pause game and open Options Menu

### Level Editor

- Mouse Click: Place selected tile

- Mouse Wheel / Up/Down Arrows: Scroll through tile menu

- ENTER: Save the current level

- ESCAPE: Return to the Main Menu

## Credits

- Pygame Community

- Assets: Treasure Hunters from pixelfrog-assets.itch.io

- Music by opengameart.org

- Font: PixelifySans