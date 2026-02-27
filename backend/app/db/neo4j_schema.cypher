// Node constraints (unique identifiers)
CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE;
CREATE CONSTRAINT event_url IF NOT EXISTS FOR (e:Event) REQUIRE e.url IS UNIQUE;
CREATE CONSTRAINT person_name_company IF NOT EXISTS FOR (p:Person) REQUIRE (p.name, p.company) IS UNIQUE;
CREATE CONSTRAINT company_name IF NOT EXISTS FOR (c:Company) REQUIRE c.name IS UNIQUE;
CREATE CONSTRAINT topic_name IF NOT EXISTS FOR (t:Topic) REQUIRE t.name IS UNIQUE;
CREATE CONSTRAINT role_name IF NOT EXISTS FOR (r:Role) REQUIRE r.name IS UNIQUE;

// Indexes for query performance
CREATE INDEX event_date IF NOT EXISTS FOR (e:Event) ON (e.date);
CREATE INDEX event_status IF NOT EXISTS FOR (e:Event) ON (e.status);
CREATE INDEX person_name IF NOT EXISTS FOR (p:Person) ON (p.name);
CREATE INDEX company_industry IF NOT EXISTS FOR (c:Company) ON (c.industry);

// Relationship types reference:
// (:User)-[:INTERESTED_IN {weight}]->(:Topic)
// (:User)-[:WANTS_TO_MEET]->(:Role)
// (:User)-[:WANTS_TO_MEET_PERSON {reason, priority, added_at}]->(:Person)
// (:User)-[:TARGETS]->(:Company)
// (:User)-[:ATTENDED {feedback, rating}]->(:Event)
// (:User)-[:REJECTED {reason, timestamp}]->(:Event)
// (:User)-[:KNOWS {strength}]->(:Person)
// (:Event)-[:HAS_SPEAKER]->(:Person)
// (:Event)-[:TAGGED]->(:Topic)
// (:Person)-[:WORKS_AT]->(:Company)
// (:Person)-[:EXPERT_IN]->(:Topic)
// (:Person)-[:CONNECTED_TO {source}]->(:Person)
// (:Company)-[:IN_INDUSTRY]->(:Topic)
