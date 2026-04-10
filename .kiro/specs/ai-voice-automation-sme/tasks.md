# Implementation Plan: AI Voice Automation for SMEs

## Overview

This implementation plan converts the AI Voice Automation system design into actionable coding tasks. The system builds upon the existing Twilio + OpenAI Realtime API integration to provide comprehensive call handling, intent detection, intelligent routing, CRM integration, and analytics for SMEs.

The implementation follows an incremental approach, starting with foundational infrastructure (database, core services), then building feature-specific components (intent detection, lead management, appointments), followed by integrations (CRM, calendar, notifications), and finally quality assurance and optimization.

## Tasks

- [ ] 1. Set up database infrastructure and core data models
  - [x] 1.1 Create PostgreSQL database schema
    - Implement all tables: calls, transcripts, leads, appointments, business_config, call_analytics, crm_sync_log
    - Add indexes for performance optimization
    - Set up foreign key constraints and cascading rules
    - _Requirements: 1.1, 5.4, 6.4, 7.2, 8.3, 15.1, 16.3_
  
  - [x] 1.2 Set up Redis configuration and connection management
    - Configure Redis client with connection pooling
    - Implement session state caching structure
    - Implement caller history caching
    - Implement agent availability caching
    - Implement configuration caching with TTL
    - _Requirements: 9.1, 9.3, 11.5, 18.2_
  
  - [x] 1.3 Create core data models and enums
    - Implement CallStatus, Intent, Language enums
    - Implement CallContext, LeadData, AppointmentData dataclasses
    - Add validation methods for data integrity
    - _Requirements: 2.3, 3.2, 5.1, 6.3, 13.1_
  
  - [ ]* 1.4 Write unit tests for data models
    - Test data validation logic
    - Test enum conversions
    - Test edge cases for optional fields
    - _Requirements: 1.1, 5.4, 6.3_

- [ ] 2. Implement Call Manager service
  - [x] 2.1 Extend SessionState to include CallContext
    - Add call_id, caller_phone, language, intent fields to SessionState
    - Add conversation_history tracking
    - Add methods for updating call context
    - _Requirements: 1.1, 1.3, 9.1, 9.2_
  
  - [x] 2.2 Create CallManager class for call lifecycle management
    - Implement call initiation and answer logic
    - Implement call state transitions (initiated → in_progress → completed)
    - Implement call termination and cleanup
    - Integrate with PostgreSQL to persist call records
    - Integrate with Redis for session caching
    - _Requirements: 1.1, 1.2, 1.4, 1.5, 18.1_
  
  - [x] 2.3 Add greeting message playback on call answer
    - Retrieve business-specific greeting from configuration
    - Play greeting within 3 seconds of call answer
    - Handle greeting completion event
    - _Requirements: 1.2, 17.1_
  
  - [ ]* 2.4 Write unit tests for CallManager
    - Test call lifecycle state transitions
    - Test concurrent call handling
    - Test database persistence
    - _Requirements: 1.1, 1.5, 18.1_

- [ ] 3. Implement Intent Detection service
  - [x] 3.1 Create IntentDetectorInterface abstract class
    - Define detect_intent method signature
    - Define request_clarification method signature
    - _Requirements: 3.1, 3.2, 3.4_
  
  - [x] 3.2 Implement OpenAIIntentDetector using function calling
    - Define intent classification function schema
    - Implement detect_intent using OpenAI Realtime API function calling
    - Parse function call results to extract intent and confidence
    - Implement intent change detection during conversation
    - _Requirements: 3.1, 3.2, 3.3, 3.5_
  
  - [x] 3.3 Add clarification request logic for low-confidence intents
    - Check if confidence score is below 0.7 threshold
    - Generate contextual clarification questions
    - Update intent after clarification response
    - _Requirements: 3.4_
  
  - [ ]* 3.4 Write property test for intent detection
    - **Property 15: Intent confidence bounds**
    - **Validates: Requirements 3.3**
    - Test that confidence scores are always between 0 and 1
  
  - [ ]* 3.5 Write unit tests for intent detection
    - Test each intent category classification
    - Test confidence score calculation
    - Test clarification triggering
    - _Requirements: 3.2, 3.3, 3.4_

- [ ] 4. Implement Call Router service
  - [x] 4.1 Create RoutingRule dataclass and CallRouter class
    - Define routing rule structure (intent, priority, business_hours_only, agent_skills, max_queue_time)
    - Implement route_call method with decision logic
    - _Requirements: 4.1, 4.2, 4.3, 4.4_
  
  - [x] 4.2 Implement business hours checking logic
    - Retrieve business hours from configuration
    - Check current time against configured hours
    - Handle timezone conversions
    - Handle holiday schedules
    - _Requirements: 4.2, 11.1, 11.2, 11.3, 11.4_
  
  - [x] 4.3 Implement agent availability checking
    - Query Redis for agent availability status
    - Match agent skills with routing requirements
    - Implement priority routing for high-value leads
    - _Requirements: 4.2, 4.4_
  
  - [x] 4.4 Add call transfer with context handoff
    - Prepare call context summary for agent
    - Initiate Twilio call transfer
    - Provide agent with caller history and intent
    - _Requirements: 4.5_
  
  - [ ]* 4.5 Write unit tests for call routing
    - Test routing decisions for each intent type
    - Test business hours logic
    - Test priority routing for high-value leads
    - _Requirements: 4.1, 4.2, 4.4_

- [x] 5. Checkpoint - Ensure core services are functional
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 6. Implement Conversation Manager enhancements
  - [x] 6.1 Add conversation history retrieval for returning callers
    - Query PostgreSQL for previous calls by phone number
    - Load conversation context from Redis cache
    - Integrate history into current conversation context
    - _Requirements: 9.1, 9.2, 9.3_
  
  - [x] 6.2 Implement multi-language detection and switching
    - Add language detection logic in first 10 seconds
    - Update OpenAI session with detected language
    - Handle language switch requests mid-conversation
    - Support English, Hindi, and 2 additional regional languages
    - _Requirements: 2.3, 13.1, 13.2, 13.3, 13.4, 13.5_
  
  - [x] 6.3 Enhance interruption handling with context preservation
    - Ensure existing interruption logic preserves conversation context
    - Resume conversation with contextually appropriate response
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_
  
  - [ ]* 6.4 Write property test for conversation context
    - **Property 28: Context persistence**
    - **Validates: Requirements 9.3**
    - Test that conversation history is maintained for 180 days

- [ ] 7. Implement Lead Manager service
  - [x] 7.1 Create LeadManager class with lead capture logic
    - Implement collect_lead_info method to gather name, phone, email, inquiry details
    - Implement lead qualification logic (budget, timeline, decision authority)
    - Implement lead scoring algorithm (1-10 scale)
    - Store lead data in PostgreSQL leads table
    - _Requirements: 5.1, 5.2, 5.3, 5.4_
  
  - [x] 7.2 Add high-value lead notification triggering
    - Check if lead score >= 7
    - Trigger immediate notification to sales team
    - _Requirements: 5.5_
  
  - [ ]* 7.3 Write property test for lead scoring
    - **Property 18: Lead score bounds**
    - **Validates: Requirements 5.3**
    - Test that lead scores are always between 1 and 10
  
  - [ ]* 7.4 Write unit tests for lead management
    - Test lead data collection
    - Test lead qualification logic
    - Test lead scoring algorithm
    - _Requirements: 5.1, 5.2, 5.3_

- [ ] 8. Implement Appointment Manager service
  - [x] 8.1 Create AppointmentManager class with calendar integration
    - Implement retrieve_available_slots method
    - Implement propose_time_slots method (minimum 3 slots)
    - Implement confirm_appointment method
    - Store appointment data in PostgreSQL appointments table
    - _Requirements: 6.1, 6.2, 6.3, 6.4_
  
  - [x] 8.2 Add appointment confirmation SMS sending
    - Integrate with Twilio SMS API
    - Send confirmation within 2 minutes of booking
    - Include appointment details (date, time, service type)
    - _Requirements: 6.5_
  
  - [ ]* 8.3 Write unit tests for appointment management
    - Test time slot retrieval
    - Test appointment confirmation
    - Test SMS sending
    - _Requirements: 6.1, 6.3, 6.5_

- [ ] 9. Implement Transcript Service
  - [x] 9.1 Create TranscriptService class for recording and transcription
    - Implement real-time audio recording in WAV format (16kHz sample rate)
    - Implement transcript generation from conversation history
    - Store recordings in S3-compatible object storage
    - Store transcript entries in PostgreSQL transcripts table
    - Associate transcripts with call metadata (timestamp, caller ID, intent, outcome)
    - _Requirements: 8.1, 8.2, 8.3, 8.4_
  
  - [~] 9.2 Add recording disclosure message playback
    - Check if recording disclosure is legally required
    - Play disclosure message before recording begins
    - _Requirements: 8.5_
  
  - [~] 9.3 Implement sensitive information masking
    - Detect and mask credit card numbers in transcripts
    - Detect and mask passwords and PINs
    - Use regex patterns for common sensitive data formats
    - _Requirements: 16.5_
  
  - [~] 9.4 Implement 90-day retention policy
    - Add cleanup job to delete recordings older than 90 days
    - Ensure compliance with data retention requirements
    - _Requirements: 8.3_
  
  - [ ]* 9.5 Write unit tests for transcript service
    - Test audio recording format
    - Test transcript generation
    - Test sensitive data masking
    - _Requirements: 8.1, 8.2, 16.5_

- [ ] 10. Checkpoint - Ensure feature services are functional
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 11. Implement CRM Integration framework
  - [~] 11.1 Create CRMIntegratorInterface abstract class
    - Define create_call_record method signature
    - Define create_lead method signature
    - Define update_contact method signature
    - _Requirements: 7.1, 7.2, 7.3_
  
  - [~] 11.2 Create CRMAdapterFactory for multi-CRM support
    - Implement factory pattern to create CRM-specific adapters
    - Support Salesforce, HubSpot, Zoho, Pipedrive
    - _Requirements: 7.4_
  
  - [~] 11.3 Implement SalesforceAdapter
    - Initialize Salesforce client with OAuth credentials
    - Implement create_call_record using Salesforce Task API
    - Implement create_lead using Salesforce Lead API
    - Implement update_contact using Salesforce Contact API
    - _Requirements: 7.1, 7.2, 7.3, 7.4_
  
  - [~] 11.4 Implement HubSpotAdapter
    - Initialize HubSpot client with API key
    - Implement create_call_record using HubSpot Engagements API
    - Implement create_lead using HubSpot Contacts API
    - Implement update_contact using HubSpot Contacts API
    - _Requirements: 7.1, 7.2, 7.3, 7.4_
  
  - [~] 11.5 Implement ZohoAdapter
    - Initialize Zoho client with OAuth credentials
    - Implement create_call_record using Zoho Calls API
    - Implement create_lead using Zoho Leads API
    - Implement update_contact using Zoho Contacts API
    - _Requirements: 7.1, 7.2, 7.3, 7.4_
  
  - [~] 11.6 Implement PipedriveAdapter
    - Initialize Pipedrive client with API token
    - Implement create_call_record using Pipedrive Activities API
    - Implement create_lead using Pipedrive Deals API
    - Implement update_contact using Pipedrive Persons API
    - _Requirements: 7.1, 7.2, 7.3, 7.4_
  
  - [~] 11.7 Add retry logic with exponential backoff
    - Implement retry decorator with max 3 attempts
    - Use exponential backoff (1s, 2s, 4s)
    - Log retry attempts in crm_sync_log table
    - _Requirements: 7.5_
  
  - [ ]* 11.8 Write property test for CRM sync
    - **Property 22: CRM sync idempotency**
    - **Validates: Requirements 7.1**
    - Test that syncing the same call multiple times produces consistent results
  
  - [ ]* 11.9 Write unit tests for CRM adapters
    - Test each adapter's create_call_record method
    - Test each adapter's create_lead method
    - Test retry logic
    - _Requirements: 7.1, 7.2, 7.5_

- [ ] 12. Implement Calendar Integration service
  - [~] 12.1 Create CalendarIntegratorInterface abstract class
    - Define get_available_slots method signature
    - Define create_event method signature
    - Define update_event method signature
    - Define delete_event method signature
    - _Requirements: 6.1, 6.4_
  
  - [~] 12.2 Implement GoogleCalendarAdapter
    - Initialize Google Calendar API client
    - Implement get_available_slots using freebusy query
    - Implement create_event for appointment booking
    - _Requirements: 6.1, 6.4_
  
  - [~] 12.3 Implement OutlookCalendarAdapter
    - Initialize Microsoft Graph API client
    - Implement get_available_slots using calendar view
    - Implement create_event for appointment booking
    - _Requirements: 6.1, 6.4_
  
  - [ ]* 12.4 Write unit tests for calendar integration
    - Test available slots retrieval
    - Test event creation
    - Test timezone handling
    - _Requirements: 6.1, 6.4_

- [ ] 13. Implement Notification Service
  - [~] 13.1 Create NotificationService class
    - Implement send_sms method using Twilio SMS API
    - Implement send_email method using SMTP or SendGrid
    - Implement send_push_notification method (placeholder for mobile app)
    - _Requirements: 19.1, 19.4_
  
  - [~] 13.2 Add notification rule configuration
    - Load notification rules from business_config
    - Filter notifications based on intent, lead score, caller identity
    - _Requirements: 19.2_
  
  - [~] 13.3 Implement escalation logic for unacknowledged notifications
    - Track notification acknowledgment status
    - Escalate to secondary contact after 5 minutes
    - _Requirements: 19.5_
  
  - [ ]* 13.4 Write unit tests for notification service
    - Test SMS sending
    - Test email sending
    - Test notification filtering
    - Test escalation logic
    - _Requirements: 19.1, 19.2, 19.5_

- [ ] 14. Implement Analytics Service
  - [~] 14.1 Create AnalyticsService class for metrics collection
    - Implement track_call_metrics method
    - Aggregate metrics: total calls, answered calls, missed calls, average duration
    - Calculate intent distribution
    - Store aggregated data in call_analytics table
    - _Requirements: 15.1_
  
  - [~] 14.2 Implement daily summary report generation
    - Generate reports with key metrics
    - Calculate call volume trends
    - Calculate peak hours
    - Calculate conversion rates
    - _Requirements: 15.2, 15.3_
  
  - [~] 14.3 Add performance alerting
    - Monitor speech recognition accuracy
    - Send alert if accuracy drops below 85%
    - Monitor response latency
    - Send alert if latency exceeds thresholds
    - _Requirements: 15.4, 18.2_
  
  - [~] 14.4 Implement data export functionality
    - Export analytics data in CSV format
    - Export analytics data in JSON format
    - _Requirements: 15.5_
  
  - [ ]* 14.5 Write unit tests for analytics service
    - Test metrics aggregation
    - Test report generation
    - Test alert triggering
    - _Requirements: 15.1, 15.2, 15.4_

- [ ] 15. Checkpoint - Ensure integration services are functional
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 16. Implement Configuration Service
  - [~] 16.1 Create ConfigService class for configuration management
    - Implement load_config method to retrieve from business_config table
    - Implement update_config method with validation
    - Implement cache invalidation on updates
    - Apply configuration changes within 2 minutes
    - _Requirements: 11.5, 17.1, 17.4, 17.5_
  
  - [~] 16.2 Add business hours configuration
    - Support per-day-of-week configuration
    - Support multiple time zones
    - Support holiday schedules
    - _Requirements: 11.1, 11.2, 11.3, 11.4_
  
  - [~] 16.3 Add AI personality and knowledge base customization
    - Allow customization of greeting message
    - Allow customization of AI personality traits
    - Support uploading business-specific knowledge bases
    - Support industry-specific terminology
    - _Requirements: 17.1, 17.2, 17.3_
  
  - [ ]* 16.4 Write unit tests for configuration service
    - Test configuration loading
    - Test configuration updates
    - Test cache invalidation
    - _Requirements: 11.5, 17.5_

- [ ] 17. Implement Error Handling and Fallback mechanisms
  - [x] 17.1 Create FallbackHandler class
    - Implement pre-recorded response tree fallback
    - Detect OpenAI API connection failures
    - Switch to fallback mode automatically
    - _Requirements: 14.1_
  
  - [x] 17.2 Add speech processing failure handling
    - Count consecutive speech recognition failures
    - Offer transfer to human agent after 3 failures
    - Offer to take a message if no agent available
    - _Requirements: 14.2_
  
  - [~] 17.3 Implement voicemail recording for system failures
    - Record voicemail when all systems fail
    - Send alert to business owner
    - Store voicemail in object storage
    - _Requirements: 14.3_
  
  - [~] 17.4 Add comprehensive error logging
    - Log all errors with timestamp, error type, call context, recovery action
    - Store error logs in PostgreSQL or dedicated logging service
    - _Requirements: 14.4_
  
  - [~] 17.5 Implement automatic service restoration
    - Detect when service is restored after outage
    - Resume normal operation automatically
    - _Requirements: 14.5_
  
  - [ ]* 17.6 Write unit tests for error handling
    - Test fallback activation
    - Test voicemail recording
    - Test automatic recovery
    - _Requirements: 14.1, 14.3, 14.5_

- [ ] 18. Implement Security and Encryption
  - [~] 18.1 Add encryption for call recordings and transcripts at rest
    - Implement AES-256 encryption for recordings before storing in S3
    - Implement AES-256 encryption for transcripts in PostgreSQL
    - Manage encryption keys securely (use AWS KMS or similar)
    - _Requirements: 16.1_
  
  - [~] 18.2 Ensure TLS 1.3 for data in transit
    - Configure TLS 1.3 for all API endpoints
    - Verify Twilio and OpenAI connections use TLS 1.3
    - _Requirements: 16.2_
  
  - [~] 18.3 Implement role-based access control (RBAC)
    - Define roles: admin, agent, viewer
    - Implement permission checks for accessing call records
    - Implement permission checks for accessing lead data
    - _Requirements: 16.3_
  
  - [~] 18.4 Add GDPR compliance features
    - Implement data deletion request handling
    - Complete deletion within 30 days
    - Ensure cascading deletion across all tables and storage
    - _Requirements: 16.4_
  
  - [ ]* 18.5 Write unit tests for security features
    - Test encryption/decryption
    - Test RBAC permission checks
    - Test data deletion
    - _Requirements: 16.1, 16.3, 16.4_

- [ ] 19. Implement Outbound Call capability
  - [~] 19.1 Create OutboundCallManager class
    - Implement initiate_call method using Twilio API
    - Support scheduled calls and trigger-based calls
    - _Requirements: 12.1_
  
  - [~] 19.2 Add answering machine detection
    - Use Twilio's AMD feature
    - Leave pre-configured voicemail message
    - _Requirements: 12.3_
  
  - [~] 19.3 Implement personalized outbound messaging
    - Retrieve call purpose from database
    - Generate personalized message based on lead data
    - Engage in conversation to achieve call objective
    - _Requirements: 12.2, 12.4_
  
  - [~] 19.4 Add do-not-call list and calling time restrictions
    - Check phone number against do-not-call list
    - Respect calling time restrictions (e.g., no calls after 9 PM)
    - _Requirements: 12.5_
  
  - [ ]* 19.5 Write unit tests for outbound calls
    - Test call initiation
    - Test AMD detection
    - Test do-not-call list checking
    - _Requirements: 12.1, 12.3, 12.5_

- [ ] 20. Implement Performance and Scalability features
  - [~] 20.1 Add connection pooling for database and Redis
    - Configure PostgreSQL connection pool (min 10, max 50 connections)
    - Configure Redis connection pool
    - _Requirements: 18.1, 18.2_
  
  - [~] 20.2 Implement call queueing for high volume
    - Detect when concurrent calls exceed capacity (50 calls)
    - Queue excess calls with estimated wait time
    - _Requirements: 18.3_
  
  - [~] 20.3 Add auto-scaling configuration
    - Configure horizontal scaling triggers (CPU, memory, call volume)
    - Support scaling up to 200% of baseline capacity
    - _Requirements: 18.4_
  
  - [~] 20.4 Implement performance monitoring
    - Track response latency for all interactions
    - Alert if 95th percentile latency exceeds 1 second
    - Track uptime and availability
    - _Requirements: 18.2, 18.5_
  
  - [ ]* 20.5 Write load tests
    - Test system with 50 concurrent calls
    - Test system with 100 concurrent calls (200% spike)
    - Measure latency and throughput
    - _Requirements: 18.1, 18.4_

- [ ] 21. Checkpoint - Ensure all features are integrated
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 22. Implement Testing and Quality Assurance features
  - [~] 22.1 Create test mode for simulating calls
    - Implement test mode flag in configuration
    - Simulate calls without using real phone numbers
    - Use mock Twilio and OpenAI connections in test mode
    - _Requirements: 20.1_
  
  - [~] 22.2 Add call playback for testing conversation flows
    - Implement playback of recorded calls
    - Allow testing conversation flow changes against historical calls
    - _Requirements: 20.2_
  
  - [~] 22.3 Implement test report generation
    - Track intent detection accuracy
    - Track response appropriateness
    - Track conversation completion rate
    - Generate comprehensive test reports
    - _Requirements: 20.3_
  
  - [~] 22.4 Add A/B testing framework
    - Randomly assign calls to conversation variants
    - Track quality metrics for each variant
    - Enable data-driven optimization
    - _Requirements: 20.4, 20.5_
  
  - [ ]* 22.5 Write integration tests
    - Test end-to-end call flow
    - Test intent detection → routing → CRM sync flow
    - Test appointment booking flow
    - _Requirements: 1.1, 3.1, 4.1, 6.1, 7.1_

- [ ] 23. Wire all components together in main application
  - [~] 23.1 Update main.py to initialize all services
    - Initialize database connections (PostgreSQL, Redis)
    - Initialize CallManager, IntentDetector, CallRouter, ConversationManager
    - Initialize LeadManager, AppointmentManager, TranscriptService
    - Initialize CRMIntegrator, CalendarIntegrator, NotificationService
    - Initialize AnalyticsService, ConfigService
    - _Requirements: All_
  
  - [~] 23.2 Update handle_media_stream to use CallManager
    - Replace SessionState with CallManager
    - Integrate intent detection into conversation flow
    - Integrate call routing decisions
    - Integrate transcript recording
    - _Requirements: 1.1, 3.1, 4.1, 8.1_
  
  - [~] 23.3 Add background tasks for async operations
    - CRM synchronization background task
    - Analytics aggregation background task
    - Notification sending background task
    - Recording cleanup background task
    - _Requirements: 7.1, 9.4, 15.1, 19.1_
  
  - [x] 23.4 Add API endpoints for configuration and management
    - POST /api/config - Update business configuration
    - GET /api/analytics - Retrieve analytics data
    - GET /api/calls - List call records
    - GET /api/leads - List leads
    - GET /api/appointments - List appointments
    - _Requirements: 15.3, 15.5, 17.1_
  
  - [ ]* 23.5 Write end-to-end integration tests
    - Test complete call flow from answer to CRM sync
    - Test lead capture and notification flow
    - Test appointment booking and confirmation flow
    - _Requirements: 1.1, 5.1, 6.1, 7.1_

- [ ] 24. Final checkpoint and deployment preparation
  - [~] 24.1 Run all tests and fix any failures
    - Run unit tests
    - Run property tests
    - Run integration tests
    - Run load tests
    - _Requirements: 20.3_
  
  - [~] 24.2 Create deployment documentation
    - Document environment variables
    - Document database setup steps
    - Document CRM integration configuration
    - Document scaling configuration
    - _Requirements: 17.1, 18.4_
  
  - [~] 24.3 Set up monitoring and alerting
    - Configure application performance monitoring (APM)
    - Set up error tracking (Sentry or similar)
    - Configure uptime monitoring
    - Set up alert channels (email, SMS, Slack)
    - _Requirements: 15.4, 18.5_
  
  - [~] 24.4 Final checkpoint - Ensure all tests pass
    - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP delivery
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- Integration tests validate end-to-end workflows
- The implementation builds incrementally: infrastructure → core services → features → integrations → quality assurance
- Checkpoints ensure validation at key milestones before proceeding
- All code examples use Python to match the existing codebase
- The system is designed for 99.5% uptime with graceful degradation on failures
