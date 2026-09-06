# API UI Cleanup Design

## Goal

Remove all provider promotion and external-link surfaces while retaining full configuration management for APIs that users have already imported.

## API Settings

- Keep the imported-provider list and every existing configuration field, including address, API key, protocol, model lists, and provider-specific operational settings.
- Rename the only creation affordance to "Import API" and continue to route it through the existing custom-provider creation flow.
- Remove the DX-OS migration banner, recommended-provider view and picker, provider onboarding promotions, affiliate/key links, CLI quick-add actions, and data-management shortcut.
- Remove the corresponding recommendation-only DOM, JavaScript, styles, translations, and external URLs so they cannot be surfaced through the page.

## Home Sidebar

- Keep API settings, theme, language, and workflow-settings controls.
- Remove GitHub/project navigation, update/download controls, version checker badge, author branding, and Bilibili, Xiaohongshu, YouTube, and X social links.

## Compatibility And Validation

- Do not alter persisted provider data, backend API routes, request protocols, or generation behavior.
- Validate that an existing provider remains editable and saveable, and that the lone Import API action creates a custom provider.
- Validate that no removed UI exposes a third-party or social URL in either light or dark theme.
