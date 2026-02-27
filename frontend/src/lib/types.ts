// === Core Types (from README Data Models) ===

export type EventSource = "eventbrite" | "luma" | "meetup" | "partiful" | "twitter" | "other";
export type EventType = "conference" | "meetup" | "dinner" | "workshop" | "happy_hour" | "demo_day";
export type EventStatus =
  | "discovered"
  | "analyzed"
  | "suggested"
  | "accepted"
  | "rejected"
  | "applied"
  | "confirmed"
  | "waitlisted"
  | "attended"
  | "skipped";
export type MessageChannel = "twitter_dm" | "linkedin" | "email" | "instagram_dm";
export type MessageStatus = "draft" | "approved" | "edited" | "sent" | "rejected";
export type MessageTone = "casual" | "professional" | "friendly";
export type TargetPriority = "high" | "medium" | "low";
export type TargetStatus = "searching" | "found_event" | "messaged" | "connected";
export type FeedbackAction = "accept" | "reject" | "edit" | "rate" | "skip";

export interface Event {
  id: string;
  url: string;
  title: string;
  source: EventSource;
  event_type: EventType;
  date: string;
  location: string;
  capacity?: number;
  price?: number;
  speakers: Person[];
  topics: string[];
  relevance_score: number;
  status: EventStatus;
  rejection_reason?: string;
  application_result?: {
    status: "applied" | "waitlisted" | "failed" | "payment_required";
    confirmation_id?: string;
    yutori_task_id: string;
  };
  calendar_event_id?: string;
  user_rating?: number;
}

export interface Person {
  id: string;
  name: string;
  title?: string;
  company?: string;
  linkedin?: string;
  twitter?: string;
  connection_score: number;
  mutual_connections: Person[];
  shared_topics: string[];
  research_summary?: string;
}

export interface ColdMessage {
  id: string;
  recipient: Person;
  event: Event;
  channel: MessageChannel;
  content: string;
  status: MessageStatus;
  user_edits?: string;
  sent_at?: string;
  response_received?: boolean;
}

export interface Feedback {
  id: string;
  user_id: string;
  event_id?: string;
  person_id?: string;
  message_id?: string;
  action: FeedbackAction;
  reason?: string;
  free_text?: string;
  rating?: number;
  created_at: string;
}

export interface TargetPerson {
  id: string;
  name: string;
  company?: string;
  role?: string;
  reason: string;
  priority: TargetPriority;
  status: TargetStatus;
  added_at: string;
  matched_events?: Event[];
}

export interface UserProfile {
  id: string;
  name: string;
  email: string;
  role: string;
  company: string;
  product_description: string;
  linkedin: string;
  twitter: string;
  networking_goals: string[];
  target_roles: string[];
  target_companies: string[];
  target_industries: string[];
  target_people: TargetPerson[];
  interests: string[];
  preferred_event_types: string[];
  max_events_per_week: number;
  max_event_spend: number;
  preferred_days: string[];
  preferred_times: string[];
  message_tone: MessageTone;
  auto_apply_threshold: number;
  suggest_threshold: number;
  auto_schedule_threshold: number;
}

// === Graph Types ===

export interface GraphNode {
  id: string;
  name: string;
  title?: string;
  company?: string;
  role?: string;
  linkedin?: string;
  twitter?: string;
  facebook?: string;
  instagram?: string;
  github?: string;
  website?: string;
  email?: string;
  avatar_color: string;
  connection_score: number;
  is_self?: boolean;
  topics: string[];
  events: string[];
  connection_count?: number;
  rank?: number;
}

export interface GraphEdge {
  source: string;
  target: string;
  strength: number;
  type: string;
}

export interface NetworkGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
  events: { id: string; title: string; url: string; date: string; location: string }[];
  user: { email: string; interests: string[] } | null;
  stats: { total_people: number; total_connections: number; total_events: number };
}

// === WebSocket Events ===

export interface WSEvents {
  "event:discovered": { event: Event };
  "event:analyzed": { event: Event; score: number };
  "event:applied": { event: Event; result: string };
  "event:scheduled": { event: Event; calendar_id: string };
  "person:discovered": { person: Person; event: Event };
  "message:drafted": { message: ColdMessage };
  "message:sent": { message: ColdMessage };
  "agent:status": { agent: string; status: string };
  "target:found": { target: TargetPerson; event: Event; person: Person };
  "target:updated": { target: TargetPerson };
}
