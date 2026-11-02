import 'package:flutter/material.dart';

import 'screens/deflection_screen.dart';
import 'screens/home_screen.dart';
import 'screens/relabel_screen.dart';

void main() => runApp(const TimeGridApp());

class TimeGridApp extends StatelessWidget {
  const TimeGridApp({super.key});

  @override
  Widget build(BuildContext context) {
    ThemeData theme(Brightness b) => ThemeData(
          colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF3F51B5), brightness: b),
          useMaterial3: true,
        );
    return MaterialApp(
      title: '시간 그리드',
      theme: theme(Brightness.light),
      darkTheme: theme(Brightness.dark),
      routes: {
        '/': (_) => const HomeScreen(),
        '/relabel': (_) => const RelabelScreen(),
        '/deflection': (_) => const DeflectionScreen(),
      },
    );
  }
}
