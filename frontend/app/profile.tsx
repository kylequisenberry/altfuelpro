import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Alert,
  Platform,
  KeyboardAvoidingView,
  Modal,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { getProfile, updateProfile, submitFeedback, FeedbackCreate } from '../src/services/api';
import { UserProfile } from '../src/types';
import { LoadingSpinner } from '../src/components/LoadingSpinner';
import { OfflineSettings } from '../src/components/OfflineSettings';
import { OfflineBanner } from '../src/components/OfflineBanner';
import { useNetworkStatus } from '../src/hooks/useNetworkStatus';
import { getLastSyncTime } from '../src/services/offlineCache';
import { COLORS, FUEL_TYPES } from '../src/constants';

const FEEDBACK_TYPES = [
  { id: 'suggestion', label: 'Suggestion', icon: 'bulb-outline', description: 'Share ideas for improvement' },
  { id: 'feature_request', label: 'Feature Request', icon: 'add-circle-outline', description: 'Request new features' },
  { id: 'support', label: 'Support', icon: 'help-circle-outline', description: 'Get help with the app' },
  { id: 'bug_report', label: 'Bug Report', icon: 'bug-outline', description: 'Report issues or problems' },
  { id: 'general', label: 'General', icon: 'chatbubble-outline', description: 'Other feedback' },
];

export default function ProfileScreen() {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [editedName, setEditedName] = useState('');
  const [editedEmail, setEditedEmail] = useState('');
  const [lastSyncTime, setLastSyncTime] = useState<Date | null>(null);
  
  // Network status
  const { isOffline } = useNetworkStatus();
  
  // Support modal state
  const [showSupportModal, setShowSupportModal] = useState(false);
  const [selectedFeedbackType, setSelectedFeedbackType] = useState<string>('suggestion');
  const [feedbackSubject, setFeedbackSubject] = useState('');
  const [feedbackMessage, setFeedbackMessage] = useState('');
  const [feedbackEmail, setFeedbackEmail] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchProfile();
    loadLastSyncTime();
  }, []);
  
  const loadLastSyncTime = async () => {
    const syncTime = await getLastSyncTime();
    setLastSyncTime(syncTime);
  };

  const fetchProfile = async () => {
    try {
      const data = await getProfile();
      setProfile(data);
      setEditedName(data.name);
      setEditedEmail(data.email || '');
      setFeedbackEmail(data.email || '');
    } catch (error) {
      console.error('Error fetching profile:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveProfile = async () => {
    try {
      const updated = await updateProfile({
        name: editedName,
        email: editedEmail,
      });
      setProfile(updated);
      setEditing(false);
      Alert.alert('Success', 'Profile updated successfully!');
    } catch (error) {
      console.error('Error updating profile:', error);
      Alert.alert('Error', 'Failed to update profile');
    }
  };

  const handleSubmitFeedback = async () => {
    if (!feedbackSubject.trim() || !feedbackMessage.trim()) {
      Alert.alert('Missing Information', 'Please fill in both subject and message');
      return;
    }

    setSubmitting(true);
    try {
      const feedback: FeedbackCreate = {
        type: selectedFeedbackType as FeedbackCreate['type'],
        subject: feedbackSubject,
        message: feedbackMessage,
        user_email: feedbackEmail || undefined,
        user_name: profile?.name,
        platform: Platform.OS,
      };

      await submitFeedback(feedback);
      
      Alert.alert(
        'Thank You!',
        'Your feedback has been submitted successfully. We appreciate your input!',
        [{ text: 'OK', onPress: () => {
          setShowSupportModal(false);
          setFeedbackSubject('');
          setFeedbackMessage('');
          setSelectedFeedbackType('suggestion');
        }}]
      );
    } catch (error) {
      console.error('Error submitting feedback:', error);
      Alert.alert('Error', 'Failed to submit feedback. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <LoadingSpinner message="Loading profile..." />;
  }

  return (
    <KeyboardAvoidingView 
      style={styles.container} 
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      {/* Offline Banner */}
      <OfflineBanner isOffline={isOffline} lastSyncTime={lastSyncTime} />
      
      <ScrollView showsVerticalScrollIndicator={false}>
        {/* Profile Header */}
        <View style={styles.header}>
          <View style={styles.avatarContainer}>
            <Ionicons name="person" size={48} color="#FFFFFF" />
          </View>
          <Text style={styles.userName}>{profile?.name || 'Guest User'}</Text>
          {profile?.email && (
            <Text style={styles.userEmail}>{profile.email}</Text>
          )}
        </View>
        
        {/* Offline Settings Section */}
        <View style={styles.section}>
          <OfflineSettings />
        </View>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Profile Information</Text>
            <TouchableOpacity onPress={() => setEditing(!editing)}>
              <Ionicons 
                name={editing ? "close" : "pencil"} 
                size={20} 
                color={COLORS.primary} 
              />
            </TouchableOpacity>
          </View>

          {editing ? (
            <View style={styles.editForm}>
              <View style={styles.inputGroup}>
                <Text style={styles.inputLabel}>Name</Text>
                <TextInput
                  style={styles.input}
                  value={editedName}
                  onChangeText={setEditedName}
                  placeholder="Enter your name"
                  placeholderTextColor={COLORS.textLight}
                />
              </View>
              <View style={styles.inputGroup}>
                <Text style={styles.inputLabel}>Email</Text>
                <TextInput
                  style={styles.input}
                  value={editedEmail}
                  onChangeText={setEditedEmail}
                  placeholder="Enter your email"
                  placeholderTextColor={COLORS.textLight}
                  keyboardType="email-address"
                  autoCapitalize="none"
                />
              </View>
              <TouchableOpacity style={styles.saveButton} onPress={handleSaveProfile}>
                <Text style={styles.saveButtonText}>Save Changes</Text>
              </TouchableOpacity>
            </View>
          ) : (
            <View style={styles.infoList}>
              <View style={styles.infoItem}>
                <Ionicons name="person-outline" size={20} color={COLORS.textSecondary} />
                <Text style={styles.infoText}>{profile?.name || 'Not set'}</Text>
              </View>
              <View style={styles.infoItem}>
                <Ionicons name="mail-outline" size={20} color={COLORS.textSecondary} />
                <Text style={styles.infoText}>{profile?.email || 'Not set'}</Text>
              </View>
            </View>
          )}
        </View>

        {/* Support Center Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Support Center</Text>
          <Text style={styles.sectionSubtitle}>
            We'd love to hear from you! Share your feedback, suggestions, or get help.
          </Text>

          <View style={styles.supportOptions}>
            <TouchableOpacity 
              style={styles.supportCard}
              onPress={() => {
                setSelectedFeedbackType('suggestion');
                setShowSupportModal(true);
              }}
            >
              <View style={[styles.supportIconContainer, { backgroundColor: '#4CAF50' + '20' }]}>
                <Ionicons name="bulb" size={24} color="#4CAF50" />
              </View>
              <Text style={styles.supportCardTitle}>Suggestion</Text>
              <Text style={styles.supportCardDesc}>Share improvement ideas</Text>
            </TouchableOpacity>

            <TouchableOpacity 
              style={styles.supportCard}
              onPress={() => {
                setSelectedFeedbackType('feature_request');
                setShowSupportModal(true);
              }}
            >
              <View style={[styles.supportIconContainer, { backgroundColor: '#2196F3' + '20' }]}>
                <Ionicons name="add-circle" size={24} color="#2196F3" />
              </View>
              <Text style={styles.supportCardTitle}>Feature Request</Text>
              <Text style={styles.supportCardDesc}>Request new features</Text>
            </TouchableOpacity>

            <TouchableOpacity 
              style={styles.supportCard}
              onPress={() => {
                setSelectedFeedbackType('support');
                setShowSupportModal(true);
              }}
            >
              <View style={[styles.supportIconContainer, { backgroundColor: '#FF9800' + '20' }]}>
                <Ionicons name="help-circle" size={24} color="#FF9800" />
              </View>
              <Text style={styles.supportCardTitle}>Get Support</Text>
              <Text style={styles.supportCardDesc}>Help with app issues</Text>
            </TouchableOpacity>

            <TouchableOpacity 
              style={styles.supportCard}
              onPress={() => {
                setSelectedFeedbackType('bug_report');
                setShowSupportModal(true);
              }}
            >
              <View style={[styles.supportIconContainer, { backgroundColor: '#F44336' + '20' }]}>
                <Ionicons name="bug" size={24} color="#F44336" />
              </View>
              <Text style={styles.supportCardTitle}>Report Bug</Text>
              <Text style={styles.supportCardDesc}>Report problems</Text>
            </TouchableOpacity>
          </View>

          <TouchableOpacity 
            style={styles.contactButton}
            onPress={() => {
              setSelectedFeedbackType('general');
              setShowSupportModal(true);
            }}
          >
            <Ionicons name="chatbubbles" size={20} color="#FFFFFF" />
            <Text style={styles.contactButtonText}>Contact Us</Text>
          </TouchableOpacity>
        </View>

        {/* App Info Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>About FuelPoint Navigator</Text>
          <View style={styles.aboutInfo}>
            <Text style={styles.aboutText}>
              Your one-stop shop for alternative fuels technical information, 
              documentation, safety, regulations, standards, and service providers.
            </Text>
            <View style={styles.versionInfo}>
              <Text style={styles.versionLabel}>Version</Text>
              <Text style={styles.versionNumber}>1.0.0</Text>
            </View>
          </View>
        </View>

        <View style={styles.bottomPadding} />
      </ScrollView>

      {/* Feedback Modal */}
      <Modal
        visible={showSupportModal}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setShowSupportModal(false)}
      >
        <KeyboardAvoidingView 
          style={styles.modalContainer}
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        >
          <View style={styles.modalHeader}>
            <TouchableOpacity onPress={() => setShowSupportModal(false)}>
              <Ionicons name="close" size={28} color={COLORS.text} />
            </TouchableOpacity>
            <Text style={styles.modalTitle}>
              {FEEDBACK_TYPES.find(t => t.id === selectedFeedbackType)?.label || 'Feedback'}
            </Text>
            <View style={{ width: 28 }} />
          </View>

          <ScrollView style={styles.modalContent} showsVerticalScrollIndicator={false}>
            {/* Feedback Type Selection */}
            <Text style={styles.modalLabel}>Type of Feedback</Text>
            <View style={styles.feedbackTypeGrid}>
              {FEEDBACK_TYPES.map((type) => (
                <TouchableOpacity
                  key={type.id}
                  style={[
                    styles.feedbackTypeButton,
                    selectedFeedbackType === type.id && styles.feedbackTypeButtonActive,
                  ]}
                  onPress={() => setSelectedFeedbackType(type.id)}
                >
                  <Ionicons 
                    name={type.icon as any} 
                    size={20} 
                    color={selectedFeedbackType === type.id ? '#FFFFFF' : COLORS.textSecondary} 
                  />
                  <Text style={[
                    styles.feedbackTypeText,
                    selectedFeedbackType === type.id && styles.feedbackTypeTextActive,
                  ]}>
                    {type.label}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            {/* Email (Optional) */}
            <Text style={styles.modalLabel}>Email (optional - for follow-up)</Text>
            <TextInput
              style={styles.modalInput}
              value={feedbackEmail}
              onChangeText={setFeedbackEmail}
              placeholder="your@email.com"
              placeholderTextColor={COLORS.textLight}
              keyboardType="email-address"
              autoCapitalize="none"
            />

            {/* Subject */}
            <Text style={styles.modalLabel}>Subject *</Text>
            <TextInput
              style={styles.modalInput}
              value={feedbackSubject}
              onChangeText={setFeedbackSubject}
              placeholder="Brief summary of your feedback"
              placeholderTextColor={COLORS.textLight}
              maxLength={100}
            />

            {/* Message */}
            <Text style={styles.modalLabel}>Message *</Text>
            <TextInput
              style={[styles.modalInput, styles.messageInput]}
              value={feedbackMessage}
              onChangeText={setFeedbackMessage}
              placeholder="Please provide details..."
              placeholderTextColor={COLORS.textLight}
              multiline
              numberOfLines={6}
              textAlignVertical="top"
              maxLength={1000}
            />
            <Text style={styles.charCount}>{feedbackMessage.length}/1000</Text>

            {/* Submit Button */}
            <TouchableOpacity 
              style={[styles.submitButton, submitting && styles.submitButtonDisabled]}
              onPress={handleSubmitFeedback}
              disabled={submitting}
            >
              {submitting ? (
                <Text style={styles.submitButtonText}>Submitting...</Text>
              ) : (
                <>
                  <Ionicons name="send" size={18} color="#FFFFFF" />
                  <Text style={styles.submitButtonText}>Submit Feedback</Text>
                </>
              )}
            </TouchableOpacity>

            <View style={styles.bottomPadding} />
          </ScrollView>
        </KeyboardAvoidingView>
      </Modal>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  header: {
    backgroundColor: COLORS.primary,
    paddingTop: 20,
    paddingBottom: 30,
    alignItems: 'center',
  },
  avatarContainer: {
    width: 88,
    height: 88,
    borderRadius: 44,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  userName: {
    fontSize: 22,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  userEmail: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.8)',
    marginTop: 4,
  },
  section: {
    backgroundColor: COLORS.surface,
    marginTop: 12,
    padding: 16,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 17,
    fontWeight: '600',
    color: COLORS.text,
  },
  sectionSubtitle: {
    fontSize: 13,
    color: COLORS.textSecondary,
    marginTop: 4,
    marginBottom: 16,
    lineHeight: 18,
  },
  infoList: {
    gap: 12,
  },
  infoItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  infoText: {
    fontSize: 15,
    color: COLORS.text,
  },
  editForm: {
    gap: 16,
  },
  inputGroup: {
    gap: 6,
  },
  inputLabel: {
    fontSize: 13,
    fontWeight: '500',
    color: COLORS.textSecondary,
  },
  input: {
    backgroundColor: COLORS.background,
    borderRadius: 8,
    padding: 12,
    fontSize: 15,
    color: COLORS.text,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  saveButton: {
    backgroundColor: COLORS.primary,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 8,
  },
  saveButtonText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '600',
  },
  supportOptions: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginBottom: 16,
  },
  supportCard: {
    width: '47%',
    backgroundColor: COLORS.background,
    padding: 14,
    borderRadius: 12,
    alignItems: 'center',
  },
  supportIconContainer: {
    width: 48,
    height: 48,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
  },
  supportCardTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.text,
    textAlign: 'center',
  },
  supportCardDesc: {
    fontSize: 11,
    color: COLORS.textSecondary,
    textAlign: 'center',
    marginTop: 2,
  },
  contactButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.primary,
    paddingVertical: 14,
    borderRadius: 10,
    gap: 8,
  },
  contactButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  aboutInfo: {
    marginTop: 8,
  },
  aboutText: {
    fontSize: 14,
    color: COLORS.textSecondary,
    lineHeight: 20,
    marginBottom: 16,
  },
  versionInfo: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: COLORS.divider,
  },
  versionLabel: {
    fontSize: 14,
    color: COLORS.textSecondary,
  },
  versionNumber: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.text,
  },
  bottomPadding: {
    height: 40,
  },
  // Modal styles
  modalContainer: {
    flex: 1,
    backgroundColor: COLORS.surface,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.divider,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.text,
  },
  modalContent: {
    flex: 1,
    padding: 16,
  },
  modalLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: 8,
    marginTop: 16,
  },
  feedbackTypeGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  feedbackTypeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 20,
    backgroundColor: COLORS.background,
    gap: 6,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  feedbackTypeButtonActive: {
    backgroundColor: COLORS.primary,
    borderColor: COLORS.primary,
  },
  feedbackTypeText: {
    fontSize: 13,
    color: COLORS.textSecondary,
  },
  feedbackTypeTextActive: {
    color: '#FFFFFF',
  },
  modalInput: {
    backgroundColor: COLORS.background,
    borderRadius: 8,
    padding: 12,
    fontSize: 15,
    color: COLORS.text,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  messageInput: {
    minHeight: 120,
    textAlignVertical: 'top',
  },
  charCount: {
    fontSize: 12,
    color: COLORS.textLight,
    textAlign: 'right',
    marginTop: 4,
  },
  submitButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.primary,
    paddingVertical: 14,
    borderRadius: 10,
    gap: 8,
    marginTop: 24,
  },
  submitButtonDisabled: {
    backgroundColor: COLORS.textLight,
  },
  submitButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
});
