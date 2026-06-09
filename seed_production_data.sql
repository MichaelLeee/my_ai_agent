-- ============================================================================
-- Production-like seed data for my_ai_agent — Complete Platform
-- Covers every entity: users, orgs, billing, RAG, chat, sessions, notes, insights
-- ~50 records per core entity with realistic names, content, and relationships.
-- ============================================================================
-- Usage:
--   docker compose -f docker-compose.dev.yml exec -T db psql -U postgres -d my_ai_agent < seed_production_data.sql
-- ============================================================================

-- Clear all existing data so this script is re-runnable
TRUNCATE users, organizations, plan CASCADE;

BEGIN;

DO $$
DECLARE
    user_ids uuid[] := ARRAY[]::uuid[];
    org_ids uuid[] := ARRAY[]::uuid[];
    conv_ids uuid[] := ARRAY[]::uuid[];
    kb_ids uuid[] := ARRAY[]::uuid[];
    note_ids uuid[] := ARRAY[]::uuid[];
    uid uuid; oid uuid; cid uuid; kid uuid; nid uuid;
    cid_ts timestamp with time zone;
BEGIN
    -- ═══════════════════════════════════════════════════════════════════════
    -- 1. USERS (50) + ORGANIZATIONS (50 personal + 3 team)
    -- ═══════════════════════════════════════════════════════════════════════
    FOR i IN 1..50 LOOP
        INSERT INTO users (id, email, full_name, role, is_active, hashed_password,
                           is_app_admin, created_at)
        VALUES (
            gen_random_uuid(),
            (ARRAY['sarah.chen','marcus.johnson','elena.rodriguez','james.wilson',
                   'aisha.patel','thomas.kim','olivia.martinez','david.thompson',
                   'nina.nguyen','alex.oconnor','maria.santos','ryan.patel',
                   'sophie.lee','kevin.brown','lisa.garcia','chris.taylor',
                   'amanda.white','jordan.harris','rachel.clark','daniel.lewis',
                   'megan.robinson','andrew.walker','jessica.hall','brandon.allen',
                   'taylor.young','sam.hernandez','kate.king','mike.wright',
                   'emma.lopez','jake.hill','laura.scott','nathan.green',
                   'haley.adams','eric.baker','anna.gonzalez','peter.nelson',
                   'carol.carter','steve.mitchell','julia.roberts','mark.turner',
                   'grace.phillips','ben.campbell','zoe.parker','dylan.evans',
                   'maya.edwards','luke.collins','aria.stewart','noah.sanchez',
                   'lily.morris','owen.rogers'])[i] || '@acme.com',
            (ARRAY['Sarah Chen','Marcus Johnson','Elena Rodriguez','James Wilson',
                   'Aisha Patel','Thomas Kim','Olivia Martinez','David Thompson',
                   'Nina Nguyen','Alex O''Connor','Maria Santos','Ryan Patel',
                   'Sophie Lee','Kevin Brown','Lisa Garcia','Chris Taylor',
                   'Amanda White','Jordan Harris','Rachel Clark','Daniel Lewis',
                   'Megan Robinson','Andrew Walker','Jessica Hall','Brandon Allen',
                   'Taylor Young','Sam Hernandez','Kate King','Mike Wright',
                   'Emma Lopez','Jake Hill','Laura Scott','Nathan Green',
                   'Haley Adams','Eric Baker','Anna Gonzalez','Peter Nelson',
                   'Carol Carter','Steve Mitchell','Julia Roberts','Mark Turner',
                   'Grace Phillips','Ben Campbell','Zoe Parker','Dylan Evans',
                   'Maya Edwards','Luke Collins','Aria Stewart','Noah Sanchez',
                   'Lily Morris','Owen Rogers'])[i],
            CASE WHEN i <= 3 THEN 'admin' ELSE 'user' END,
            true,
            '$2b$12$HzSzVWrnrw4mgQAh5YbKXe93FLzJs2GouE4xh4GLnhCqjeezUKd9y',
            i <= 2,
            now() - (random() * interval '180 days'))
        RETURNING id INTO uid;
        user_ids := array_append(user_ids, uid);

        -- Personal org for every user
        INSERT INTO organizations (id, name, slug, is_personal, created_by_user_id,
                                   subscription_tier, created_at)
        VALUES (gen_random_uuid(), 'Personal', 'personal-' || i::text, true,
                uid, 'free', now())
        RETURNING id INTO oid;
        org_ids := array_append(org_ids, oid);

        INSERT INTO organization_members (id, organization_id, user_id, role, joined_at)
        VALUES (gen_random_uuid(), oid, uid, 'owner', now());
    END LOOP;

    -- 3 team orgs
    FOR i IN 1..3 LOOP
        INSERT INTO organizations (id, name, slug, is_personal, created_by_user_id,
                                   subscription_tier, created_at)
        VALUES (gen_random_uuid(),
                (ARRAY['Engineering','Product','Design'])[i],
                (ARRAY['engineering','product','design'])[i],
                false, user_ids[i], 'pro', now())
        RETURNING id INTO oid;

        -- Add 5-8 members per team org
        FOR j IN 0..(5 + (random() * 3)::int) LOOP
            <<member_block>>
            DECLARE
                member_uid uuid := user_ids[1 + ((i * 10 + j) % array_length(user_ids,1))];
            BEGIN
                INSERT INTO organization_members (id, organization_id, user_id, role, joined_at)
                VALUES (gen_random_uuid(), oid, member_uid,
                        CASE WHEN j = 0 THEN 'owner'
                             WHEN j <= 2 THEN 'admin' ELSE 'member' END,
                        now() - (random() * interval '90 days'));
            EXCEPTION WHEN unique_violation THEN NULL; END;
        END LOOP;
    END LOOP;

    -- ═══════════════════════════════════════════════════════════════════════
    -- 2. BILLING — Plans & Prices
    -- ═══════════════════════════════════════════════════════════════════════
    DECLARE
        plan_free_id uuid; plan_pro_id uuid; plan_team_id uuid;
    BEGIN
        INSERT INTO plan (id, code, display_name, description, is_active, sort_order,
                          features, base_amount_cents, included_seats, extra_seat_amount_cents,
                          seats_min, seats_max, monthly_credits_base, monthly_credits_per_seat,
                          created_at)
        VALUES (gen_random_uuid(), 'free', 'Free',
                '100 notes, 10 AI searches/day, basic agent', true, 1,
                '{"notes":100,"searches_per_day":10,"rag":false,"insights":false,"teams":false}',
                0, 1, 0, 1, NULL, 100, 0, now())
        RETURNING id INTO plan_free_id;

        INSERT INTO plan (id, code, display_name, description, is_active, sort_order,
                          features, base_amount_cents, included_seats, extra_seat_amount_cents,
                          seats_min, seats_max, monthly_credits_base, monthly_credits_per_seat,
                          created_at)
        VALUES (gen_random_uuid(), 'pro', 'Pro',
                'Unlimited notes, AI search, RAG, Insights — for power users', true, 2,
                '{"notes":"unlimited","searches":"unlimited","rag":true,"insights":true,"teams":false}',
                1500, 1, 0, 1, NULL, 2000, 500, now())
        RETURNING id INTO plan_pro_id;

        INSERT INTO plan (id, code, display_name, description, is_active, sort_order,
                          features, base_amount_cents, included_seats, extra_seat_amount_cents,
                          seats_min, seats_max, monthly_credits_base, monthly_credits_per_seat,
                          created_at)
        VALUES (gen_random_uuid(), 'team', 'Team',
                'Everything in Pro plus shared knowledge bases, admin controls', true, 3,
                '{"notes":"unlimited","searches":"unlimited","rag":true,"insights":true,"teams":true}',
                3000, 5, 1000, 1, NULL, 5000, 1000, now())
        RETURNING id INTO plan_team_id;

        -- Prices for each plan
        INSERT INTO price (id, plan_id, stripe_price_id, interval, amount_cents, currency,
                           billing_scheme, is_active, created_at)
        VALUES
        (gen_random_uuid(), plan_free_id, 'price_free_monthly', 'month', 0, 'usd', 'per_unit', true, now()),
        (gen_random_uuid(), plan_pro_id, 'price_pro_monthly', 'month', 1500, 'usd', 'per_unit', true, now()),
        (gen_random_uuid(), plan_pro_id, 'price_pro_yearly', 'year', 14400, 'usd', 'per_unit', true, now()),
        (gen_random_uuid(), plan_team_id, 'price_team_monthly', 'month', 3000, 'usd', 'per_unit', true, now()),
        (gen_random_uuid(), plan_team_id, 'price_team_yearly', 'year', 28800, 'usd', 'per_unit', true, now());

        -- Give Pro subscriptions to the team orgs
        INSERT INTO subscription (id, organization_id, stripe_subscription_id, stripe_customer_id,
                                  stripe_item_id, price_id, seats_quantity, status,
                                  current_period_start, current_period_end,
                                  cancel_at_period_end, created_at)
        SELECT gen_random_uuid(), o.id, 'sub_dev_' || o.slug, 'cus_dev_' || o.slug,
               'si_dev_' || o.slug,
               (SELECT id FROM price WHERE interval = 'month' AND plan_id = plan_pro_id LIMIT 1),
               5, 'active', now() - interval '15 days', now() + interval '15 days',
               false, now()
        FROM organizations o WHERE o.is_personal = false;
    END;

    -- ═══════════════════════════════════════════════════════════════════════
    -- 3. KNOWLEDGE BASES / RAG (50)
    -- ═══════════════════════════════════════════════════════════════════════
    FOR i IN 1..50 LOOP
        INSERT INTO knowledge_bases (id, name, description, scope, collection_name, is_default,
                                     owner_user_id, organization_id, created_at)
        VALUES (
            gen_random_uuid(),
            (ARRAY['Work Docs','Research Papers','Meeting Notes','Product Specs','Design Files',
                   'Engineering Wiki','Onboarding','Company Policies','Sales Playbook','Marketing Assets',
                   'Legal Docs','HR Handbook','Security Policies','API Docs','Architecture Decisions',
                   'Post-mortems','Runbooks','Playbooks','Templates','Competitive Intel',
                   'User Research','A/B Test Results','Customer Interviews','Support KB','FAQ',
                   'Release Notes','Changelog','Blog Drafts','Social Media','Email Templates',
                   'Investor Updates','Board Decks','Financial Models','OKRs','Roadmaps',
                   'Sprint Plans','Retrospectives','1-on-1 Notes','Performance Reviews','Training Materials',
                   'Code Reviews','Design Reviews','Product Reviews','Technical Specs','Data Models',
                   'Migration Plans','Incident Reports','Vendor Evaluations','Patent Ideas','Innovation Log'])[i],
            'Collection for ' || (ARRAY['Work Docs','Research Papers','Meeting Notes','Product Specs','Design Files',
                   'Engineering Wiki','Onboarding','Company Policies','Sales Playbook','Marketing Assets',
                   'Legal Docs','HR Handbook','Security Policies','API Docs','Architecture Decisions',
                   'Post-mortems','Runbooks','Playbooks','Templates','Competitive Intel',
                   'User Research','A/B Test Results','Customer Interviews','Support KB','FAQ',
                   'Release Notes','Changelog','Blog Drafts','Social Media','Email Templates',
                   'Investor Updates','Board Decks','Financial Models','OKRs','Roadmaps',
                   'Sprint Plans','Retrospectives','1-on-1 Notes','Performance Reviews','Training Materials',
                   'Code Reviews','Design Reviews','Product Reviews','Technical Specs','Data Models',
                   'Migration Plans','Incident Reports','Vendor Evaluations','Patent Ideas','Innovation Log'])[i],
            CASE WHEN i <= 3 THEN 'org' ELSE 'personal' END,
            'kb_' || i::text || '_' || floor(random() * 99999)::text,
            i <= 4,
            CASE WHEN i <= 3 THEN NULL ELSE user_ids[1 + (i % 10)] END,  -- first 10 users
            CASE WHEN i <= 3 THEN org_ids[array_length(org_ids,1) - 3 + i] ELSE NULL END,
            now() - (random() * interval '120 days'))
        RETURNING id INTO kid;
        kb_ids := array_append(kb_ids, kid);
    END LOOP;

    -- ═══════════════════════════════════════════════════════════════════════
    -- 4. SESSIONS (50 login sessions)
    -- ═══════════════════════════════════════════════════════════════════════
    FOR i IN 1..50 LOOP
        INSERT INTO sessions (id, user_id, refresh_token_hash, device_name, device_type,
                              ip_address, is_active, created_at, last_used_at, expires_at)
        VALUES (
            gen_random_uuid(),
            user_ids[1 + (i % 10)],  -- first 10 users for rich demo
            '$2b$12$' || md5(random()::text || clock_timestamp()::text),
            (ARRAY['MacBook Pro','iPhone 15','ThinkPad X1','iPad Air','Dell XPS',
                   'Pixel 8','MacBook Air','Galaxy S24','Surface Laptop','Framework 13',
                   'Custom Desktop','Mac Studio','iPhone 14 Pro','Samsung Galaxy Book','iPad Pro',
                   'Lenovo Legion','HP Spectre','Google Pixelbook','Mac Mini','Razer Blade',
                   'iPhone SE','OnePlus 12','ASUS Zenbook','Nothing Phone','Xiaomi 14'])[1 + (i % 25)],
            (ARRAY['desktop','mobile','desktop','tablet','desktop'])[1 + (i % 5)],
            '192.168.1.' || (i + 10)::text,
            random() < 0.8,
            now() - (random() * interval '30 days'),
            now() - (random() * interval '2 days'),
            now() + interval '30 days'
        );
    END LOOP;

    -- ═══════════════════════════════════════════════════════════════════════
    -- 5. CONVERSATIONS (30) + MESSAGES (3-10 per conversation)
    -- ═══════════════════════════════════════════════════════════════════════
    FOR i IN 1..30 LOOP
        INSERT INTO conversations (id, user_id, organization_id, title, is_archived, created_at)
        VALUES (
            gen_random_uuid(),
            user_ids[1 + (i % 10)],  -- first 10 users for rich demo
            org_ids[1 + (i % 10)],
            (ARRAY['Q3 planning discussion','Debugging the deployment','Ideas for Second Brain',
                   'API design brainstorming','Weekly check-in','Bug investigation',
                   'Feature roadmap review','Code review session','Architecture deep dive',
                   'Customer feedback analysis','Team standup notes','Hiring pipeline review',
                   'Performance optimization','Security audit prep','Launch planning',
                   'Design critique','Data migration strategy','Onboarding improvements',
                   'Cost optimization chat','Competitive analysis','User interview prep',
                   'Retrospective','Sprint planning','1-on-1 catch-up','RAG tuning',
                   'Extension brainstorm','Pricing discussion','Investor pitch practice',
                   'OKR review','Weekend hack session'])[i],
            random() < 0.15,
            now() - (random() * interval '60 days'))
        RETURNING id, created_at INTO cid, cid_ts;
        conv_ids := array_append(conv_ids, cid);

        -- 3-10 messages per conversation
        FOR j IN 1..(3 + (random() * 7)::int) LOOP
            INSERT INTO messages (id, conversation_id, role, content, model_name, tokens_used, created_at)
            VALUES (
                gen_random_uuid(), cid,
                CASE WHEN j % 2 = 1 THEN 'user' ELSE 'assistant' END,
                CASE WHEN j % 2 = 1 THEN
                    (ARRAY['Can you help me think through this?',
                           'What do you think about using pgvector for this?',
                           'I need to refactor the auth module. Where should I start?',
                           'Search my notes about deployment strategies',
                           'Summarize what I wrote about the API migration',
                           'Create a note about the architecture decision we just discussed',
                           'What are the tradeoffs between JWT and session auth?',
                           'How do I optimize this query?',
                           'Remind me what we decided about the database schema',
                           'What did I journal about last week?',
                           'Can you link the deployment note to the docker note?',
                           'Show me my weekly summary',
                           'I think we should use Redis for caching',
                           'What are my most-used tags this month?',
                           'Draft an email to the team about the new feature'])[1 + (j % 15)]
                ELSE
                    (ARRAY['Based on your notes, here are the key considerations...',
                           'I found 3 related notes in your Second Brain. The most relevant one...',
                           'That''s an interesting point. Let me search your knowledge base...',
                           'I''ve created a note summarizing this discussion.',
                           'Here''s what your architecture notes say about this topic...',
                           'Your recent journal entries suggest you''ve been focused on deployment.',
                           'Looking at your note history, you made a similar decision in March.',
                           'I''ve linked these two notes — they appear to be related.',
                           'Your weekly summary is ready. Top themes: architecture, deployment.',
                           'I noticed a pattern: you''ve mentioned pgvector in 7 notes this month.',
                           'Here are the tradeoffs based on your existing architecture...',
                           'That contradicts a claim you made in a note from last month.',
                           'Good call. I''ve saved this as a decision note.',
                           'Your morning briefing: 3 unread insights about deployment.',
                           'Based on your codebase, I recommend starting with the auth middleware.'])[1 + (j % 15)]
                END,
                CASE WHEN j % 2 = 0 THEN 'claude-opus-4-7' ELSE NULL END,
                CASE WHEN j % 2 = 0 THEN (100 + random() * 2000)::int ELSE NULL END,
                cid_ts + (j * interval '2 minutes')
            );
        END LOOP;
    END LOOP;

    -- ═══════════════════════════════════════════════════════════════════════
    -- 6. INVITATIONS (20)
    -- ═══════════════════════════════════════════════════════════════════════
    FOR i IN 1..20 LOOP
        <<invite_block>>
        DECLARE
            invite_org_id uuid := org_ids[array_length(org_ids,1) - 3 + 1 + (i % 3)];
            inviter_uid uuid := user_ids[1 + (i % 5)];
            invite_email text := 'newuser' || i::text || '@example.com';
        BEGIN
            INSERT INTO invitations (id, organization_id, email, role, invited_by_user_id,
                                     token, status, expires_at, created_at)
            VALUES (
                gen_random_uuid(), invite_org_id, invite_email,
                CASE WHEN i % 3 = 0 THEN 'admin' ELSE 'member' END,
                inviter_uid,
                md5(random()::text || clock_timestamp()::text),
                CASE WHEN i <= 15 THEN 'accepted' WHEN i <= 18 THEN 'pending' ELSE 'expired' END,
                now() + interval '7 days',
                now() - (random() * interval '90 days')
            );
        END;
    END LOOP;

    -- ═══════════════════════════════════════════════════════════════════════
    -- 7. USER SLASH COMMANDS (50)
    -- ═══════════════════════════════════════════════════════════════════════
    FOR i IN 1..50 LOOP
        BEGIN
            INSERT INTO user_slash_commands (id, user_id, name, prompt, is_enabled, created_at)
            VALUES (
                gen_random_uuid(),
                user_ids[1 + (i % 10)],  -- first 10 users for rich demo
                (ARRAY['summarize','explain','refactor','review','draft','translate',
                       'debug','optimize','document','test','deploy','analyze',
                       'compare','recommend','calculate','schedule','remind','search',
                       'teach','brainstorm','prioritize','estimate','format','validate',
                       'extract','convert','merge','split','archive','restore',
                       'backup','migrate','audit','monitor','alert','report',
                       'track','log','notify','sync','import','export',
                       'publish','share','collaborate','approve','reject','escalate',
                       'onboard','offboard'])[i],
                'When I use /' || (ARRAY['summarize','explain','refactor','review','draft','translate',
                       'debug','optimize','document','test','deploy','analyze',
                       'compare','recommend','calculate','schedule','remind','search',
                       'teach','brainstorm','prioritize','estimate','format','validate',
                       'extract','convert','merge','split','archive','restore',
                       'backup','migrate','audit','monitor','alert','report',
                       'track','log','notify','sync','import','export',
                       'publish','share','collaborate','approve','reject','escalate',
                       'onboard','offboard'])[i] || ', ' ||
                (ARRAY['give me a concise summary','explain step by step','suggest improvements',
                       'find issues and suggest fixes','write a clear draft','translate the following',
                       'help debug this error','suggest performance improvements','generate documentation',
                       'write unit tests','create a deployment plan','analyze this data',
                       'compare these options','recommend the best approach','calculate the result',
                       'add to my schedule','set a reminder for','search my knowledge base',
                       'teach me about','help me brainstorm ideas','prioritize these tasks',
                       'give me a rough estimate','format this properly','validate this input',
                       'extract key information','convert this format','merge these together',
                       'split this into parts','archive old items','restore from backup',
                       'create a backup','plan the migration','audit for issues',
                       'set up monitoring','create an alert','generate a report',
                       'track my progress','log this event','send a notification',
                       'sync with external source','import from file','export to format',
                       'publish this draft','share with the team','start a collaboration',
                       'review and approve','reject with feedback','escalate to manager',
                       'help onboard new team member','offboard departing user'])[i],
                random() < 0.7,
                now() - (random() * interval '90 days'))
            ;
        EXCEPTION WHEN unique_violation THEN NULL; END;
    END LOOP;

    -- ═══════════════════════════════════════════════════════════════════════
    -- 8. CUSTOM INSTRUCTIONS (50)
    -- ═══════════════════════════════════════════════════════════════════════
    FOR i IN 1..50 LOOP
        BEGIN
            INSERT INTO custom_instructions (id, user_id, name, content, is_active, created_at)
            VALUES (
                gen_random_uuid(),
                user_ids[1 + ((i - 1) % 5)],  -- anchor to first 5 users for rich demo experience
                (ARRAY['Always respond in German','Be concise and direct','Use bullet points','Explain like I''m 5',
                       'Act as a senior engineer','Use formal language','Include code examples',
                       'Speak like a pirate','Be encouraging and supportive','Show pros and cons',
                       'Use markdown formatting','Act as a product manager','Think step by step',
                       'Suggest alternatives','Keep responses under 3 paragraphs',
                       'Use analogies and metaphors','Act as a DevOps expert','Prioritize security',
                       'Be data-driven','Use humor when appropriate',
                       'Always cite sources','Act as a CTO advisor','Focus on scalability',
                       'Write production-ready code','Review for edge cases','Optimize for readability',
                       'Act as a UX reviewer','Suggest testing strategies','Prefer functional patterns',
                       'Use TypeScript examples','Act as a database expert','Explain architecture tradeoffs',
                       'Keep it conversational','Be opinionated','Include documentation links',
                       'Act as a startup founder','Challenge my assumptions','Summarize at the end',
                       'Use diagrams (ASCII art)','Focus on cost optimization','Consider mobile-first',
                       'Act as a hiring manager','Think about accessibility','Prioritize user experience',
                       'Use real-world examples','Act as a security auditor','Suggest monitoring approaches',
                       'Follow industry best practices','Be brutally honest','End with next steps'])[i],
                (ARRAY['Antworte immer auf Deutsch. Verwende formelle Anrede (Sie) und deutsche Beispiele.',
                       'Give me the shortest answer that fully addresses my question. No fluff, no preamble, no summary.',
                       'Always format your responses as bullet points. Use nested bullets for sub-points. No paragraphs.',
                       'Explain concepts like I''m 5 years old. Use simple words, fun analogies, and avoid jargon entirely.',
                       'Respond as a senior software engineer with 15 years of experience. Include architecture considerations, trade-offs, and production war stories.',
                       'Use formal, professional language. Address me as a colleague. Avoid contractions and casual expressions.',
                       'Always include runnable code examples in your responses. Show input and expected output. Prefer Python or TypeScript.',
                       'Respond as a pirate would. Use "Arr!", "matey", "me hearties" and nautical metaphors throughout.',
                       'Be warm, encouraging, and supportive. Acknowledge effort, celebrate progress, and frame feedback positively.',
                       'For every decision or recommendation, present the pros and cons in a structured format before giving your opinion.',
                       'Format all responses using proper markdown: headers, code blocks, tables, and lists where appropriate.',
                       'Act as an experienced product manager. Think about user stories, acceptance criteria, and prioritization frameworks.',
                       'For complex problems, break down your reasoning step by step before reaching a conclusion.',
                       'For every solution you propose, also mention 2-3 alternative approaches and why you didn''t choose them.',
                       'Keep every response to 3 short paragraphs maximum. If you need more, use a TL;DR at the top.',
                       'Explain technical concepts using everyday analogies and metaphors. Make the abstract tangible.',
                       'Act as a DevOps and infrastructure expert. Think about deployment, monitoring, scaling, and reliability.',
                       'Always evaluate security implications first. Consider OWASP top 10, data privacy, and attack surfaces.',
                       'Support every claim with data or metrics. When data isn''t available, clearly state your assumptions.',
                       'Use appropriate humor and wit in your responses, but never at the expense of clarity or correctness.',
                       'Always cite specific sources (docs, articles, RFCs) when making technical claims. Link when possible.',
                       'Act as a strategic CTO advisor. Think about long-term implications, team dynamics, and business value.',
                       'Always consider how solutions scale to 10x, 100x, 1000x. Discuss bottlenecks and breaking points.',
                       'Write code that is production-ready: includes error handling, logging, tests, and clear documentation.',
                       'Review all code for edge cases: empty input, nil/null values, large datasets, concurrent access.',
                       'Optimize code primarily for readability and maintainability. Performance comes second unless it''s a bottleneck.',
                       'Review all UI and API designs from a user experience perspective. Suggest improvements for clarity and flow.',
                       'Suggest appropriate testing strategies: unit, integration, e2e, property-based, fuzzing as relevant.',
                       'When writing code, prefer functional programming patterns: pure functions, immutability, composition over inheritance.',
                       'Provide code examples in TypeScript with strict mode. Use modern ES features and proper typing throughout.',
                       'Act as a database and data modeling expert. Think about schema design, query optimization, and data integrity.',
                       'When comparing architectures or approaches, explain the fundamental tradeoffs and what you''d choose and why.',
                       'Keep your tone conversational and friendly, like we''re colleagues chatting over coffee. No corporate speak.',
                       'Be opinionated and decisive. Don''t just list options — tell me which one you''d pick and defend your choice.',
                       'Include links to relevant documentation, official guides, or well-known blog posts in your responses.',
                       'Act as a Y Combinator startup founder. Think about MVPs, product-market fit, growth, and fundraising.',
                       'Actively challenge my assumptions and decisions. Play devil''s advocate. Push me to think deeper.',
                       'End every response with a brief summary of key takeaways and recommended next actions.',
                       'Use ASCII art diagrams to visualize architectures, flows, and relationships when explaining systems.',
                       'Always consider the cost implications: infrastructure, engineering time, operational overhead, vendor lock-in.',
                       'Consider mobile and responsive design first. Think about touch targets, screen sizes, and offline support.',
                       'Act as an experienced engineering hiring manager. Evaluate decisions through the lens of team building and culture.',
                       'Always consider accessibility (a11y): screen readers, keyboard navigation, color contrast, semantic HTML.',
                       'Prioritize user experience in all recommendations. Think about the person using the software, not just the code.',
                       'Use concrete real-world examples from well-known companies or open-source projects to illustrate your points.',
                       'Act as a security auditor reviewing the system. Look for vulnerabilities, misconfigurations, and compliance gaps.',
                       'Suggest monitoring, observability, and alerting approaches for any system you help design or review.',
                       'Follow industry best practices and standards. Reference RFCs, design patterns, and community conventions.',
                       'Be brutally honest. Don''t sugarcoat. If something is a bad idea, say so clearly and explain why.',
                       'End every response with 3 specific, actionable next steps I can take immediately.'])[i],
                random() < 0.25,  -- ~25% active at a time
                now() - (random() * interval '90 days'))
            ;
        EXCEPTION WHEN unique_violation THEN NULL; END;
    END LOOP;

    -- ═══════════════════════════════════════════════════════════════════════
    -- 9. NOTES (50) + NOTE LINKS + INSIGHTS
    -- ═══════════════════════════════════════════════════════════════════════
    DECLARE
        notes_data text[][] := ARRAY[
            ['Q3 Product Strategy', 'Three pillars: agent performance, multi-tenant isolation, dev experience. Agent latency <500ms p95. Row-level security by August. Better docs, SDK, playground.', '["decision","product","strategy"]'],
            ['pgvector Migration Retro', 'Completed pgvector migration. 40% faster search, eliminated ChromaDB. HNSW index builds ~2min for 100K vectors cold start.', '["database","devops","retrospective"]'],
            ['Auth Architecture Decision', 'JWT access tokens (15min) + refresh (7d httpOnly). API keys via X-API-Key with bcrypt. Fully stateless backend.', '["architecture","auth","decision"]'],
            ['Monday Journal', 'Reviewed reflection loop code. Auto-linker working but 0.7 threshold too aggressive. Need tuning. Wrote entity extraction spec.', '["journal"]'],
            ['Voyage AI Embedding Notes', 'voyage-3-large, 1024 dims, $0.06/1M tokens. Free tier 200M tokens, 3 RPM limit (22s delay in seeds).', '["ai","embeddings","cost"]'],
            ['Competitor Analysis - Personal AI', 'Mem.ai (good search, weak agent), Reflect (great journaling, no RAG), Rewind (privacy issues). Our edge: proactive reflection loop.', '["strategy","competitive","research"]'],
            ['Frontend Performance', 'Lighthouse LCP 2.1s from graph simulation. Fix: reduce initial nodes, add Web Worker later.', '["frontend","performance","optimization"]'],
            ['Knowledge Graph UX Research', '5 user test: love connections but overwhelmed >30 nodes. Need tag filter + dashed/solid edge patterns.', '["ux","research","frontend"]'],
            ['Docker Compose Setup Guide', 'Dev: db+redis+celery in Docker, uv run for backend, bun dev for frontend. Ports: 8080/3030/5433/6379. pgvector image required.', '["docker","devops","docs"]'],
            ['Weekly Architecture Review', 'Decisions: link_type on note_links, entity extraction in reflection worker, SVG for graph accessibility, briefing at 7AM.', '["architecture","weekly","decision"]'],
            ['Database Indexing Strategy', 'Indexes: users(email), notes(user_id), note_links(source,target), custom_instructions(user_id). Missing: GIN on tags, created_at on insights.', '["database","optimization"]'],
            ['API Rate Limiting Design', 'Token bucket per-user via Redis. 100/min chat, 30/min CRUD, 10/min RAG. Admin 5x. Headers: X-RateLimit-*.', '["api","security","architecture"]'],
            ['Team Onboarding Process', 'Steps: clone+make bootstrap, register, get invited to org, set Voyage key, run seeds, read arch doc, first task.', '["team","onboarding"]'],
            ['Deployment Checklist v2', 'Pre: rotate SECRET_KEY, ENVIRONMENT=production, SMTP, Sentry DSN, alembic upgrade head, /health verify. Post: monitor 15min.', '["deployment","devops","checklist"]'],
            ['Security Audit Findings', 'Good: API keys bcrypt. Issues: JWT rotation missing, CORS too open, rate limit only on chat. All fixable.', '["security","audit"]'],
            ['LLM Cost Optimization', 'Monthly: Claude $42, Voyage $3. Ideas: cache common queries, batch embed, model routing. Target 30% savings.', '["ai","cost","optimization"]'],
            ['Reflection Loop Performance', '50 users×100 notes: ~45s/user sequential. Fix: asyncio.gather in parallel batches of 10.', '["performance","worker","optimization"]'],
            ['User Interview - Sarah Chen', 'Wants: better search with date ranges, bulk operations, note templates. Pain: "I know I wrote it but can''t find it."', '["ux","research","user-feedback"]'],
            ['Mobile PWA Architecture', 'PWA with service worker, IndexedDB drafts, background sync. Minimal UI: title+content+voice. No chat, capture only.', '["mobile","architecture","pwa"]'],
            ['RAG Pipeline Improvements', 'Improvements: hybrid BM25+vector, Cohere reranking, metadata filtering (date/tag), citation highlighting.', '["rag","search","improvement"]'],
            ['Venture Pitch Draft', 'Personal knowledge OS. Unlike Notion (docs) or ChatGPT (stateless), builds living knowledge graph with proactive agent.', '["strategy","pitch"]'],
            ['API Key Management Design', 'sk_ + 43 chars, bcrypt hash, prefix lookup + constant-time compare. Soft-delete revocation. Created via slash commands.', '["api","security","design"]'],
            ['WebSocket Reconnection Logic', 'Exponential backoff 1s→30s max. Heartbeat every 30s, timeout 60s. Replay queued messages on reconnect.', '["websocket","frontend","reliability"]'],
            ['Analytics Dashboard Design', 'Metrics: DAU/WAU, notes/user/week, convos/day, searches/session, insight accept rate. Postgres + materialized views.', '["analytics","metrics"]'],
            ['Design System Component Audit', 'Current: Button,Input,Textarea,Card,Dialog,Badge. Missing: DataTable for admin. Using sonner + cmdk externally.', '["frontend","design-system"]'],
            ['Error Handling Patterns', 'Domain exceptions→service→exception handlers→HTTP. Frontend: apiClient catch→toast. Worker: Celery retry backoff.', '["architecture","errors","patterns"]'],
            ['Testing Strategy Update', 'Backend 60%, frontend 30%. Target: 80/60 by Q3. Gaps: agent tools, worker integration, graph component, extension.', '["testing","quality"]'],
            ['Git Branch Strategy', 'feature/<name> from main, one per feature, merge after local test. No staging. Main always deployable. Tag v2.x releases.', '["devops","git","workflow"]'],
            ['Customer Success Playbook', 'Onboarding: 15min call, daily journal check-in W1, auto-link review W2, weekly summary W4. 5+ journals in W1 = 90% retention.', '["business","customer-success"]'],
            ['Pricing Model Exploration', 'Free (100 notes,10 searches), Pro $15/mo (unlimited,RAG,Insights), Team $30/seat. Target 5% conversion, $12 ARPU at 10K users.', '["business","pricing"]'],
            ['Weekly Retrospective', 'Shipped: reflection loop, knowledge graph, browser extension. 3 features in 4 days. Pain: Docker+alembic DX needs work.', '["journal","weekly","retrospective"]'],
            ['On-call Runbook', 'Response: Sentry→docker ps→celery logs→Redis→Postgres pool. Escalation: p95>2s for 5min or error>5%.', '["devops","runbook","on-call"]'],
            ['Hiring - Senior Frontend', 'React 19, Next.js 15, TS, Tailwind, D3/vis. Process: phone→take-home(data viz)→system design(real-time)→culture fit.', '["hiring","team","frontend"]'],
            ['Wednesday Standup Notes', 'Sarah: rate limiting PR. Marcus: entity extraction merged. Elena: PWA+voice. James: 30% LLM savings. Blockers: Voyage prod key.', '["standup","team"]'],
            ['Conference Talk Abstract', 'Building a Personal AI That Thinks With You. RAG arch, agent tools, knowledge graph visualization. Augments thinking, not replaces it.', '["speaking","conference"]'],
            ['Browser Extension UX', 'Auto-fills title from page. Pre-selects recent tags. One-click save. Options: full page, selection only, URL only. Ctrl+Shift+S.', '["extension","ux","browser"]'],
            ['Note Organization Taxonomy', 'PARA method: Projects>Areas>Resources>Archives. Project tags get sidebar+graph filter. Freeform+project tags hybrid.', '["organization","taxonomy","design"]'],
            ['Privacy Architecture', 'Encryption at rest (Postgres TDE), TLS in transit. Embeddings stored separately. Hard delete within 30 days. GDPR/CCPA ready.', '["privacy","security","compliance"]'],
            ['Graph Algorithm Tuning', 'Repulsion 500, attraction 0.01, decay 0.98, 200 iterations. 50+ nodes: reduce to 100 iter, increase repulsion to 800.', '["algorithms","graph","optimization"]'],
            ['Content Marketing Strategy', 'Posts: "Second Brain in 4 Days", "Why Notes Need Knowledge Graphs", "Reflection Loop Explained". Channels: HN, Reddit, Twitter.', '["marketing","content","growth"]'],
            ['Accessibility Audit', 'WCAG 2.1 AA: keyboard nav works, graph not keyboard-accessible, edge legend contrast 2.8:1 (need 3:1), no ARIA on SVG.', '["accessibility","audit","frontend"]'],
            ['Investor Update - June', 'MRR: $0 (pre-launch). Active dev users: 3. Features shipped: 10. Next: entity extraction, mobile PWA. Raising $500K pre-seed.', '["business","investors"]'],
            ['Grafana Dashboard Setup', 'Panels: API latency, error rate, celery tasks, pgvector latency, LLM cost, WebSocket conns, DB pool. Alerts on all thresholds.', '["monitoring","devops","grafana"]'],
            ['Data Migration Script', 'Import from: Markdown files (Joplin/Obsidian), JSON (Notion API), CSV (Apple Notes). Preserves: title, content, date, tags. Dedup by hash.', '["data","migration","tooling"]'],
            ['User Permission Model', 'Current: user owns everything. Future: shared notes (read-only link), collaborative spaces (org KB), public notes. Viewer→editor→owner.', '["permissions","authorization","design"]'],
            ['Environment Variable Guide', 'Required: DATABASE_URL, REDIS_URL, SECRET_KEY, ANTHROPIC_API_KEY, VOYAGE_API_KEY. Optional: SENTRY_DSN, SMTP_*, STRIPE_*. Rotate SECRET_KEY quarterly.', '["devops","security","config"]'],
            ['E2E Test Scenarios', 'Critical: register→login→create note→search→delete. Chat→agent creates note. Custom instruction verified. Reflection loop→insights. Link notes→graph edge.', '["testing","e2e","quality"]'],
            ['Sprint Planning - Week 24', 'Goals: typed links, entity extraction v1, graph legend. Stretch: D3 migration. Capacity: 35pts. Risk: Voyage prod key. No blockers.', '["sprint","planning","team"]'],
            ['Personal PKM Philosophy', 'Capture what matters, let the rest go. System: quick capture (5s), weekly review (cull+tag+link), monthly synthesis, quarterly archive.', '["philosophy","pkm","personal"]'],
            ['Friday Wrap-up', 'Shipped typed links! link_type live on note_links. Graph: green(supports), red(contradicts), amber(depends_on), grey(relates_to). Entity extraction found patterns.', '["journal","weekly"]']
        ];
        n text[];
    BEGIN
        FOREACH n SLICE 1 IN ARRAY notes_data LOOP
            INSERT INTO notes (id, user_id, title, content, tags, is_archived, created_at, updated_at)
            VALUES (gen_random_uuid(),
                    user_ids[1 + (random() * 9)::int],  -- first 10 users for rich demo experience
                    n[1], n[2],
                    n[3]::jsonb,
                    false,
                    now() - (random() * interval '60 days'),
                    now())
            RETURNING id INTO nid;
            note_ids := array_append(note_ids, nid);
        END LOOP;

        -- NOTE LINKS (50, typed)
        DECLARE
            link_types text[] := ARRAY['supports','contradicts','depends_on','relates_to'];
        BEGIN
            FOR i IN 1..50 LOOP
                <<link_block>>
                DECLARE
                    s_id uuid := note_ids[1 + (random() * (array_length(note_ids,1)-1))::int];
                    t_id uuid;
                BEGIN
                    LOOP
                        t_id := note_ids[1 + (random() * (array_length(note_ids,1)-1))::int];
                        EXIT WHEN t_id != s_id;
                    END LOOP;
                    BEGIN
                        INSERT INTO note_links (id, source_note_id, target_note_id, link_type, created_at, updated_at)
                        VALUES (gen_random_uuid(), s_id, t_id,
                                link_types[1 + (random() * 3)::int],
                                now() - (random() * interval '30 days'), now());
                    EXCEPTION WHEN unique_violation THEN NULL; END;
                END;
            END LOOP;
        END;

        -- INSIGHTS (50)
        DECLARE
            insight_types text[] := ARRAY['connection','pattern','contradiction','suggestion','summary'];
        BEGIN
            FOR i IN 1..50 LOOP
                INSERT INTO insights (id, user_id, type, title, content, related_note_ids,
                                      is_read, is_dismissed, created_at, updated_at)
                VALUES (
                    gen_random_uuid(),
                    user_ids[1 + (random() * 9)::int],  -- first 10 users for rich demo
                    insight_types[1 + (random() * 4)::int],
                    (ARRAY['Notes about deployment connected','Architecture pattern detected',
                           'Possible contradiction found','Consider archiving old entries',
                           'Weekly synthesis','Database notes clustering',
                           'AI optimization pattern','Frontend performance gap',
                           'Security topic trending','DevOps workflow consolidation',
                           'Team notes linked','API design patterns',
                           'Cost optimization opportunity','UX research insights',
                           'Testing coverage gaps','Hiring pipeline pattern',
                           'Mobile strategy alignment','Privacy review needed',
                           'Docs need update','Monitoring gaps found',
                           'Knowledge graph growing','Reflection loop healthy',
                           'Morning briefing','Weekly review',
                           'New RAG connection','Entity extraction results',
                           'Link: docker + deployment','Journal habit pattern',
                           'Q3 priorities check','Tag cleanup suggested',
                           'Architecture discussions trending','Monitoring + grafana linked',
                           'Onboarding template needed','Security improvements pattern',
                           'Frontend + performance link','Cost reduction pattern',
                           'D3 migration suggestion','Mobile + PWA connection',
                           'Testing improvements pattern','Pricing model review',
                           'Extension + capture link','Taxonomy doc needed',
                           'Conference talk pattern','Investor update connection',
                           'Monday briefing','Tuesday briefing',
                           'Wednesday briefing','Thursday briefing',
                           'Friday briefing','Weekend reflection'])[i],
                    'Auto-generated by the reflection loop. Based on analysis of recent notes, links, and activity patterns.',
                    to_jsonb(ARRAY[note_ids[1 + (random() * (array_length(note_ids,1)-1))::int]::text,
                          note_ids[1 + (random() * (array_length(note_ids,1)-1))::int]::text]),
                    random() < 0.4, random() < 0.1,
                    now() - (random() * interval '14 days'), now()
                );
            END LOOP;
        END;
    END;

    RAISE NOTICE 'Seeded platform data: 50 users, 53 orgs, 50 KBs, 50 sessions, 30 conversations, 50 slash-commands, 20 invitations, 3 plans, 50 notes with typed links and insights.';
END $$;

COMMIT;
