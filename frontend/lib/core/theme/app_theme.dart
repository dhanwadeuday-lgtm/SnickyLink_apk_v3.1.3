import 'package:flutter/material.dart';

class AppTheme {
  // SnickyLink Wine & Peach design system.
  static const Color mutedWine = Color(0xFF6B2B3C);
  static const Color deepWineBlack = Color(0xFF3A1620);
  static const Color warmPeach = Color(0xFFE8B99C);
  static const Color blushWhite = Color(0xFFFBF4F1);
  static const Color inkWine = Color(0xFF1E0E13);

  // Backwards-compatible aliases used by existing feature code.
  static const Color copperRose = mutedWine;
  static const Color dayBackground = blushWhite;
  static const Color nightBackground = inkWine;

  static ThemeData get lightTheme => ThemeData(
        useMaterial3: true,
        brightness: Brightness.light,
        scaffoldBackgroundColor: blushWhite,
        colorScheme: const ColorScheme.light(
          primary: mutedWine,
          secondary: warmPeach,
          surface: Colors.white,
          onPrimary: Colors.white,
          onSecondary: deepWineBlack,
        ),
        appBarTheme: const AppBarTheme(
          backgroundColor: blushWhite,
          foregroundColor: deepWineBlack,
          elevation: 0,
        ),
        cardTheme: CardThemeData(
          color: Colors.white,
          elevation: 1,
          shadowColor: deepWineBlack,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.all(Radius.circular(20)),
          ),
        ),
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: Colors.white,
          border: OutlineInputBorder(
            borderRadius: BorderRadius.all(Radius.circular(16)),
            borderSide: BorderSide.none,
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.all(Radius.circular(16)),
            borderSide: BorderSide(color: mutedWine, width: 1.5),
          ),
        ),
      );

  static ThemeData get darkTheme => ThemeData(
        useMaterial3: true,
        brightness: Brightness.dark,
        scaffoldBackgroundColor: inkWine,
        colorScheme: const ColorScheme.dark(
          primary: warmPeach,
          secondary: mutedWine,
          surface: deepWineBlack,
          onPrimary: deepWineBlack,
          onSecondary: Colors.white,
        ),
        appBarTheme: const AppBarTheme(
          backgroundColor: inkWine,
          foregroundColor: Colors.white,
          elevation: 0,
        ),
        cardTheme: const CardThemeData(
          color: deepWineBlack,
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.all(Radius.circular(20)),
          ),
        ),
        inputDecorationTheme: const InputDecorationTheme(
          filled: true,
          fillColor: deepWineBlack,
          border: OutlineInputBorder(
            borderRadius: BorderRadius.all(Radius.circular(16)),
            borderSide: BorderSide.none,
          ),
        ),
      );
}
