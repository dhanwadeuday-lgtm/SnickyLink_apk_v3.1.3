import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'core/theme/app_theme.dart';
import 'features/auth/presentation/screens/login_screen.dart';
import 'features/auth/presentation/screens/signup_screen.dart';
import 'features/auth/presentation/screens/splash_screen.dart';
import 'features/home/presentation/screens/home_screen.dart';
import 'features/chat/presentation/screens/chat_screen.dart';
import 'features/memories/presentation/screens/memories_screen.dart';
import 'features/calendar/presentation/screens/calendar_screen.dart';
import 'features/community/presentation/screens/community_screen.dart';
import 'features/profile/presentation/screens/profile_screen.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const ProviderScope(child: SnickyLinkApp()));
}

class SnickyLinkApp extends StatelessWidget {
  const SnickyLinkApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'SnickyLink',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: ThemeMode.system,
      routes: {
        '/': (_) => const SplashScreen(),
        '/login': (_) => const LoginScreen(),
        '/signup': (_) => const SignupScreen(),
        '/home': (_) => const HomeScreen(),
        '/chat': (_) => const ChatScreen(),
        '/memories': (_) => const MemoriesScreen(),
        '/calendar': (_) => const CalendarScreen(),
        '/community': (_) => const CommunityScreen(),
        '/profile': (_) => const ProfileScreen(),
      },
      initialRoute: '/',
    );
  }
}
