# Designing the UI (WYSIWYG)

Development is done on **macOS and/or Linux**. You can design the MEGA Get GUI in a drag-and-drop or visual way using these tools, then integrate the generated Flet code into the FletX app.

## FletDesigner

[FletDesigner](https://github.com/normalentity/FletDesigner) — Open-source drag-and-drop UI builder for Flet. Use it to design screens and export or copy Flet code, then integrate the generated widgets/layout into [app/pages/mega_page.py](../flet-app/app/pages/mega_page.py) or into [app/components/](../flet-app/app/components/).

## LabDeck Flet GUI Designer

[LabDeck Flet GUI Designer](https://labdeck.com/flet-tutorial/flet-gui-designer/) — Drag-and-drop WYSIWYG for Flet; can generate Python/Flet code. Use it for layout and styling, then adapt the generated code into your FletX page or component.

## Workflow

1. Design the UI in FletDesigner or LabDeck (layout, controls, styling).
2. Export or copy the generated Flet control tree (e.g. `ft.Row`, `ft.Column`, `ft.TextField`, `ft.Button`).
3. Paste or adapt the code into `MegaPage.build()` in [app/pages/mega_page.py](../flet-app/app/pages/mega_page.py), or into a reusable component under [app/components/](../flet-app/app/components/).
4. Bind the UI to controller state with FletX’s `@obx` decorator and controller methods (e.g. `ctrl.log_content.value`, `ctrl.on_get`, `ctrl.on_cancel`).

The app uses [FletX](https://github.com/AllDotPy/FletX) (GetX-inspired) for reactive state and controllers; the page’s `build()` and `_build_log()` already wire the log and buttons to [MegaController](../flet-app/app/controllers/mega_controller.py).
