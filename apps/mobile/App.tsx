import React from "react";
import { SafeAreaView, StyleSheet, Text, View } from "react-native";
import { StatusBar } from "expo-status-bar";

export default function App() {
  return (
    <SafeAreaView style={styles.root}>
      <StatusBar style="light" />
      <View style={styles.card}>
        <Text style={styles.wordmark}>NUR</Text>
        <Text style={styles.title}>Mobile shell is ready for native wiring.</Text>
        <Text style={styles.body}>
          The production-ready path is the PWA today. This Expo surface is a real
          checked-in native starting point, but it does not claim app-store readiness.
        </Text>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: "#020103", alignItems: "center", justifyContent: "center", padding: 24 },
  card: { width: "100%", maxWidth: 420, borderColor: "rgba(255,224,142,0.24)", borderWidth: 1, borderRadius: 24, padding: 24, backgroundColor: "rgba(15,7,7,0.86)" },
  wordmark: { color: "#ffe5a8", fontSize: 56, letterSpacing: 12, textAlign: "center" },
  title: { color: "#fff0c8", fontSize: 24, marginTop: 18, textAlign: "center" },
  body: { color: "rgba(255,240,212,0.72)", fontSize: 17, lineHeight: 24, marginTop: 12, textAlign: "center" },
});
