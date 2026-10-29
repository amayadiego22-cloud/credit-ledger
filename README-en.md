<p align="center">
  <img src="docs/cover-0.22.11-302x170.png" alt="Credit Ledger — Credit goals and battle accounting" width="302" height="170">
</p>

# Credit Ledger — 0.22.11

[Español](README.md) · [Download with installer](https://github.com/amayadiego22-cloud/credit-ledger/releases/tag/v0.22.11) · [WGMods](https://wgmods.net/8056/)

## Interface preview

![Credit Ledger garage widget and circular goal progress](docs/01-widget-circle-0.22.11.png)

Choose the expanded panel or the compact progress circle. The Move handle appears when you hover over it.

<details>
<summary><strong>View screenshots: details, filters and daily history</strong></summary>

### Details in English

![Credit goals and account details in English](docs/03-details-en-0.22.11.png)

### Details in Spanish

![Credit goals and account details in Spanish](docs/02-details-es-0.22.11.png)

### Battle breakdown and filters

![Game mode and vehicle filters, tank images, income and expenses](docs/04-battle-filters-0.22.11.png)

### Daily battle history

![Daily battle history with recorded battles and filters](docs/05-daily-history-0.22.11.png)

</details>

*These are the same 0.22.11 interface previews published on WGMods. Amounts shown are demonstration data.*

The entire circle highlights on hover, including its outer edge. Click anywhere on the disk to expand, or drag the Move handle to reposition it. Highlighting does not change the actual goal percentage.

Version 0.22.11 applies the approved goal circle: a thicker green ring, percentage, target amount and “Goal” label inside a 112 × 112 px disk. The transparent window includes a “Move” handle that appears on hover or keyboard navigation and remains visible while dragging. Click the center to expand. New accounts start with a **100,000 additional-credit goal** based on their synced balance. Existing saved goals, including disabled goals, remain unchanged. History resets still disable the goal. Progress bars are thicker and green. The player confirmed the circle and full hover highlight in the game on 0.22.11. This release has no beta label and includes the installer inside the ZIP.

Release 0.22.8 gives the mod and installer a shared 8pt layout: 8/16/24/32px spacing, aligned cards, clearer controls and a less crowded widget. Goals, history and financial calculations are preserved. Validation passed 432 Python tests, 117 rendered UI checks and 32 installer tests. The player subsequently confirmed the 0.22.11 circle in the game; the live confirmations below refer to earlier releases.

For **Wargaming World of Tanks PC: Americas (NA), Europe (EU) and Asia (ASIA), clients 2.4.1.0 and 2.4.1.1**.

This release limits the widget and details to the actual garage view. They hide when you open the tech tree, Service Record or another page and return automatically when you return to the garage. Clients **2.4.1.0 and 2.4.1.1** remain supported on NA, EU and ASIA. 432 tests passed; seven native navigation contracts are identical across the three installed 2.4.1.1 clients. Earlier live accounting tests used NA, EU and Asia on 2.4.1.0; the player has confirmed this fix on 2.4.1.1 using the tech tree, Service Record and return to the garage. This is not a claim of new connected tests on all three regions. Lesta/Mir Tankov and Blitz are not supported.

The minimized state and saved positions are retained. Accounting continues while other pages are open; navigating never resets your goal or history.

The ZIP installs identical mod files at `mods/2.4.1.0/local.credit_ledger.wotmod` and `mods/2.4.1.1/local.credit_ledger.wotmod`. The game loads only its active version's folder. Accounting, optional goals, filters and saved local data retain the same behavior.

Credit Ledger tracks your battle income, expenses and profit or loss after costs. A movable garage widget shows your credit goal; **View details** opens the full breakdown. The mod reads native battle results and your synchronized account balance. It does not change your actual credits.

**Daily battle history** now has a clear gold **[+] / [−]** control. **+** expands the history and **−** collapses it; the whole header is clickable and keyboard accessible.

Mode icons are larger: 40 pixels in filters and selected battle details, and 24 pixels alongside each battle in the history list. The five-battle viewport, wheel scrolling and scrollbar are preserved for current and archived days.

Native modes 14 and 15 are now identified as **Tournament Battle** and **Clan Tournament**, using the client's special-battle emblem. Their names update in current filters, individual battle details and daily history, including existing records. Amounts and battle identities are preserved.

## Choose your language

The interface starts in **Spanish**. Open **Ver detalles**, then select **English** beside the button that returns to the widget. The entire interface switches immediately, without restarting the game, and your preference is saved for future sessions. Select **Español** to switch back.

English uses comma separators for credit amounts, such as **1,000,000**, and a decimal point for percentages, such as **45.5%**. Spanish uses **1.000.000** and **45,5 %**. The underlying amounts do not change. Vehicle and mission names follow the language supplied by your game client.

Changing the language preserves your goal, unsaved goal amount, filters, selected battle, history and account balance. If saving the preference fails, the interface reports the problem and lets you retry.

## Goals and daily results

Your goal is the number of **additional credits** you want to earn. For example, starting at 22,000,000 credits with a 3,000,000 goal means you begin at 0% and finish at 25,000,000.

- Updating the goal amount keeps your original starting balance and accumulated progress.
- Enter **0** to turn the goal off. Your progress reference remains available during the same tracking period.
- Use the separate goal reset button to start a new goal from your current balance without clearing battles.
- The arrows change the goal by 100,000 credits. You can also type an amount.

The widget stays available in the garage. Its corner circle minimizes it to a live progress ring; click anywhere on the disk to restore it, or use the hover-only Move handle to reposition it. Drag the expanded widget by its header. It is hidden during battles. Clicks outside the panel remain available to the garage.

When you reach a new goal, a green **“Goal reached! Well done!”** message and a few small sparks appear for 2.8 seconds inside the widget, then disappear automatically. It waits for the garage, vehicle and widget to finish loading and remain visible for 1.5 seconds before starting. An achievement is acknowledged only after the full presentation; if loading or hiding the window interrupts it, it remains pending. In the details view, the message appears in the goal area. The effect does not resize the window or block its controls. If the widget is minimized, the pending celebration waits until you show a view. Already acknowledged achievements do not replay on refresh, language changes or a later session. A new goal can celebrate again, as can a higher target when you reach it. Goals that were already complete when this feature was first installed are recognized silently. Reduced-motion environments receive the static message.

The battle breakdown can be filtered by **game mode and vehicle**. Each battle shows the tank's native image, name and tier, its mode, gross income, expenses and final profit or loss. Positive values are green, negative values red and zero neutral. Tank comparison rankings are not included.

Personal and clan reserve bonuses appear as separate breakdown rows. They are **already included in gross income** and are never added twice. A dash means an older captured result does not contain that optional detail; its known income and expenses remain available. An actual zero is displayed as zero.

## Daily battle history

At each new **server game day**, current battle statistics restart at zero and the goal is turned off. The new tracking period uses your current synchronized balance. This is built in and does not require choosing a local reset time. Reconnecting during the same server day does not reset the period again.

The manual history reset button remains available with confirmation. It resets the current period and deactivates the goal while preserving your real account balance and captured evidence.

**Daily battle history** is collapsed at the bottom of the details panel. Open it to select an earlier recorded day, then filter by game mode or tank. Browsing earlier days does not change today's goal or statistics. Additional identified rewards are shown separately for the whole day because they cannot safely be assigned to a specific tank or mode.

The archive contains **only results captured by the mod**, not a download of your account's entire history. Each selection displays its latest 100 battles, with five complete rows before scrolling. Totals include every recorded battle in that selection. Older captured days are retained.

## Missions and account balance

Identified mission rewards and other credits are tracked using native receipts. Rewards already included in a battle are annotated without being counted twice. Purchases, sales and other movements without an identified receipt appear as other account movements. Goals follow the real change in your synchronized balance, including those movements.

## Installation and updates

Close the game completely and extract the public ZIP into its main folder, merging the `mods` folder. The installed package is:

```text
<GAME_FOLDER>\mods\2.4.1.1\local.credit_ledger.wotmod
<GAME_FOLDER>\mods\2.4.1.0\local.credit_ledger.wotmod
```

The same download targets NA, EU and ASIA with clients 2.4.1.0 and 2.4.1.1. The game loads only the file in its active version's folder. Account data stays under `mods\configs\credit_ledger`; captures are separated under `captures\<REALM>\<account>`. The server-day reset uses the connected client's native daily boundary. Update by replacing this mod's files while the game is closed, keeping one copy in each client-version folder. Account data and other mods are preserved.

Download updates from the official portal listing. The public player ZIP contains no account data, external updater, service or scheduled task. To uninstall, remove only the `.wotmod` while the game is closed; local data is retained. Local development uses a separate windowless update helper, which is not part of the public package.

The mod source is original. Python code is compiled with the installed client's Python 2.7 DLL; that DLL and standalone game artwork are not redistributed. Automated regional checks cover NA, EU and ASIA. Earlier connected live-client testing on NA used the previous client version; no live 2.4.1.1 validation is claimed here. The interface remains Spanish/English, selectable instantly without a restart.
