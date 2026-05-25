import React from 'react';
import {
  View, Text, StyleSheet, SafeAreaView, StatusBar
} from 'react-native';
import TeacherBottomNav from '../components/TeacherBottomNav';

const BLUE = '#2952e3';

export default function TeacherStudentsScreen({ navigation }) {
  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar barStyle="dark-content" backgroundColor="#f5f7fa" />
      <View style={styles.container}>
        <View style={styles.card}>
          <Text style={styles.icon}>👥</Text>
          <Text style={styles.title}>Students</Text>
          <Text style={styles.subtitle}>Coming Soon</Text>
          <Text style={styles.description}>
            The student roster and management interface is being prepared. Soon you will be able to view and manage all student details from this tab.
          </Text>
        </View>
      </View>
      <TeacherBottomNav navigation={navigation} active="Students" />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: '#f5f7fa' },
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 24,
  },
  card: {
    backgroundColor: '#ffffff',
    borderRadius: 24,
    padding: 32,
    alignItems: 'center',
    width: '100%',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.08,
    shadowRadius: 12,
    elevation: 4,
  },
  icon: { fontSize: 48, marginBottom: 16 },
  title: { fontSize: 24, fontWeight: '800', color: '#1a1f36', marginBottom: 8 },
  subtitle: { fontSize: 16, fontWeight: '700', color: BLUE, marginBottom: 16 },
  description: {
    fontSize: 14,
    color: '#6b7280',
    textAlign: 'center',
    lineHeight: 20,
  },
});
