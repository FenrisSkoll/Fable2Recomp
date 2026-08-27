// fable2 - ReXGlue Recompiled Project
//
// Customize your app by overriding virtual hooks from rex::ReXApp.

#pragma once

#include <rex/rex_app.h>

#if defined(REXGLUE_ENABLE_FAULT_WALK) ||                                      \
    defined(REXGLUE_ENABLE_FAULT_WALK_DISPATCH)
#include <rex/fault_walk.h>
#endif

class Fable2App : public rex::ReXApp {
public:
  using rex::ReXApp::ReXApp;

  static std::unique_ptr<rex::ui::WindowedApp>
  Create(rex::ui::WindowedAppContext &ctx) {
    return std::unique_ptr<Fable2App>(
        new Fable2App(ctx, "fable2", PPCImageConfig));
  }

  void OnPostInitLogging() override {
#if defined(REXGLUE_ENABLE_FAULT_WALK)
    rex::diagnostics::InitializeFaultWalk(
        rex::diagnostics::FaultWalkMode::Full);
#elif defined(REXGLUE_ENABLE_FAULT_WALK_DISPATCH)
    rex::diagnostics::InitializeFaultWalk(
        rex::diagnostics::FaultWalkMode::DispatchOnly);
#endif
  }

  // Override virtual hooks for customization:
  // void OnPreSetup(rex::RuntimeConfig& config) override {}
  // void OnLoadXexImage(std::string& xex_image) override {}
  // void OnPostLoadXexImage() override {}
  // void OnPostSetup() override {}
  // void OnCreateDialogs(rex::ui::ImGuiDrawer* drawer) override {}
  // std::unique_ptr<rex::ui::ImGuiDialog> CreateAchievementsOverlay() override;
  // std::unique_ptr<rex::ui::AchievementNotificationDialog>
  // CreateAchievementNotificationDialog() override;
  // void OnShutdown() override {}
  // void OnConfigurePaths(rex::PathConfig& paths) override {}
};
