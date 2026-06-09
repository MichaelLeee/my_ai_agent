"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowUpRight,
  Brain,
  Hash,
  Lightbulb,
  Link2,
  List,
  MessageSquare,
  Search,
  Star,
  TrendingUp,
  Zap,
} from "lucide-react";
import { ActiveSessions } from "@/components/dashboard/active-sessions";
import { OnboardingBanner } from "@/components/dashboard/onboarding-banner";
import { QuickActions } from "@/components/dashboard/quick-actions";
import { RecentActivity } from "@/components/dashboard/recent-activity";
import { StatCard } from "@/components/dashboard/stat-card";
import { SubscriptionChip } from "@/components/dashboard/subscription-chip";
import { TeamSummary } from "@/components/dashboard/team-summary";
import { useAuth } from "@/hooks";
import { apiClient } from "@/lib/api-client";
import { ROUTES } from "@/lib/constants";
import { cn } from "@/lib/utils";
import type { HealthResponse } from "@/types";

interface DashboardData {
  stats: {
    total_notes: number;
    total_links: number;
    unread_insights: number;
    journal_streak: number;
    journal_this_week: number;
  };
  top_tags: Array<{ tag: string; count: number }>;
  recent_activity: Array<{
    type: string;
    id: string;
    title: string;
    insight_type?: string;
    timestamp: string | null;
  }>;
  insights_summary: Record<string, number>;
}

function getGreeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}

export default function DashboardPage() {
  const { user } = useAuth();
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState(false);
  const [dash, setDash] = useState<DashboardData | null>(null);
  const [dashLoading, setDashLoading] = useState(true);

  useEffect(() => {
    apiClient
      .get<HealthResponse>("/health")
      .then((d) => {
        setHealth(d);
        setHealthError(false);
      })
      .catch(() => setHealthError(true));

    apiClient
      .get<DashboardData>("/v1/dashboard")
      .then(setDash)
      .catch(() => {})
      .finally(() => setDashLoading(false));
  }, []);

  const firstName = user?.full_name?.split(" ")[0] || user?.email?.split("@")[0];

  return (
    <div className="space-y-6 pb-8">
      <OnboardingBanner />

      {/* HERO BLOCK — greeting + status pulse */}
      <div className="grid gap-4 lg:grid-cols-[1.5fr_1fr]">
        {/* Greeting card */}
        <div className="border-foreground/10 bg-foreground/[0.02] relative isolate overflow-hidden rounded-3xl border p-7 sm:p-9">
          <div
            aria-hidden
            className="pointer-events-none absolute -top-24 -right-24 -z-10 h-[340px] w-[340px] rounded-full blur-3xl"
            style={{
              background:
                "radial-gradient(circle, oklch(from var(--color-brand) l c h / 0.28), transparent 65%)",
            }}
          />
          <div
            aria-hidden
            className="bg-dots pointer-events-none absolute inset-0 -z-10 opacity-50"
          />

          <p className="text-foreground/55 font-mono text-[11px] tracking-wider uppercase">
            Dashboard
          </p>
          <h1 className="font-display text-foreground [&_em]:font-accent mt-2 text-3xl leading-[1.05] font-bold tracking-tight sm:text-4xl [&_em]:font-normal [&_em]:italic">
            {getGreeting()}
            {firstName ? (
              <>
                ,<br />
                <em>{firstName}.</em>
              </>
            ) : (
              <span className="text-foreground/30">.</span>
            )}
          </h1>
          <p className="text-foreground/65 mt-4 max-w-md text-sm">
            Here&apos;s what&apos;s happening with your Second Brain.
          </p>

          <div className="mt-7 flex flex-wrap items-center gap-3">
            <Link
              href={ROUTES.CHAT}
              className="bg-foreground text-background hover:bg-foreground/90 group inline-flex items-center gap-3 rounded-full py-2 pr-2 pl-5 text-sm font-medium transition-colors"
            >
              <span>New chat</span>
              <span className="bg-brand text-brand-foreground flex h-8 w-8 items-center justify-center rounded-full transition-transform group-hover:rotate-45">
                <ArrowUpRight className="h-3.5 w-3.5" />
              </span>
            </Link>
            <SearchHint />
          </div>
        </div>

        {/* Status pulse card */}
        <div className="border-foreground/10 bg-foreground/[0.02] relative flex flex-col justify-between gap-6 overflow-hidden rounded-3xl border p-6 sm:p-7">
          <div>
            <p className="text-foreground/55 mb-4 font-mono text-[11px] tracking-wider uppercase">
              Status
            </p>
            <div className="flex items-center gap-3">
              <span
                aria-hidden
                className={cn(
                  "inline-block h-2 w-2 rounded-full",
                  healthError ? "bg-destructive" : "bg-brand animate-pulse",
                )}
                style={
                  healthError
                    ? undefined
                    : { boxShadow: "0 0 14px var(--color-brand), 0 0 4px var(--color-brand)" }
                }
              />
              <span className="font-display text-foreground text-lg font-semibold">
                {healthError ? "API offline" : health?.status || "Operational"}
              </span>
            </div>
            {health?.version && (
              <p className="text-foreground/45 mt-1 ml-5 font-mono text-[10px] tracking-wider uppercase">
                v{health.version}
              </p>
            )}
          </div>

          <dl className="space-y-2.5 text-xs">
            <div className="flex items-center justify-between">
              <dt className="text-foreground/55 font-mono tracking-wider uppercase">Notes</dt>
              <dd className="text-foreground font-mono tabular-nums">
                {dashLoading ? "—" : (dash?.stats.total_notes ?? 0).toLocaleString()}
              </dd>
            </div>
            <div className="flex items-center justify-between">
              <dt className="text-foreground/55 font-mono tracking-wider uppercase">Insights</dt>
              <dd className="text-foreground font-mono tabular-nums">
                {dashLoading ? "—" : (dash?.stats.unread_insights ?? 0).toLocaleString()}
              </dd>
            </div>
            <div className="flex items-center justify-between">
              <dt className="text-foreground/55 font-mono tracking-wider uppercase">Plan</dt>
              <dd>
                <SubscriptionChip />
              </dd>
            </div>
          </dl>
        </div>
      </div>

      {/* SECOND BRAIN METRICS */}
      <div className="flex items-center justify-between">
        <h2 className="text-foreground/55 font-mono text-[11px] tracking-wider uppercase">
          Second Brain
        </h2>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Notes"
          value={dashLoading ? "—" : (dash?.stats.total_notes ?? 0).toLocaleString()}
          icon={Brain}
          loading={dashLoading}
        />
        <StatCard
          label="Links"
          value={dashLoading ? "—" : (dash?.stats.total_links ?? 0).toLocaleString()}
          icon={Link2}
          loading={dashLoading}
        />
        <StatCard
          label="Insights"
          value={dashLoading ? "—" : (dash?.stats.unread_insights ?? 0).toLocaleString()}
          delta={dash?.stats.unread_insights ? dash.stats.unread_insights : undefined}
          icon={Lightbulb}
          loading={dashLoading}
        />
        <StatCard
          label="Journal streak"
          value={dashLoading ? "—" : (dash?.stats.journal_streak ?? 0).toLocaleString()}
          unit="days"
          icon={Zap}
          loading={dashLoading}
        />
      </div>

      {/* Activity + insights sidebar */}
      <div className="grid gap-4 lg:grid-cols-[1.4fr_1fr]">
        <RecentActivity />

        {/* Top tags + insight summary sidebar */}
        <div className="space-y-4">
          {/* Top tags */}
          {dash?.top_tags && dash.top_tags.length > 0 && (
            <div className="border-foreground/10 bg-foreground/[0.02] rounded-2xl border p-5">
              <p className="text-foreground/55 mb-3 font-mono text-[10px] tracking-wider uppercase">
                Top tags
              </p>
              <div className="flex flex-wrap gap-1.5">
                {dash.top_tags.map(({ tag, count }) => (
                  <span
                    key={tag}
                    className="border-foreground/15 bg-foreground/5 text-foreground/75 hover:border-foreground/30 inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs transition-colors"
                  >
                    {tag}
                    <span className="text-foreground/40 font-mono text-[10px]">{count}</span>
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Insight summary */}
          {dash?.insights_summary && Object.keys(dash.insights_summary).length > 0 && (
            <div className="border-foreground/10 bg-foreground/[0.02] rounded-2xl border p-5">
              <p className="text-foreground/55 mb-3 font-mono text-[10px] tracking-wider uppercase">
                Insights
              </p>
              <div className="space-y-2">
                {Object.entries(dash.insights_summary).map(([type, count]) => (
                  <div key={type} className="flex items-center justify-between text-sm">
                    <span className="text-foreground/70 capitalize">{type}</span>
                    <span className="text-foreground/50 font-mono text-xs">{count}</span>
                  </div>
                ))}
              </div>
              {dash?.insights_summary && Object.keys(dash.insights_summary).length > 0 && (
                <Link
                  href="/second-brain"
                  className="text-brand hover:text-brand/80 mt-3 inline-flex items-center gap-1 text-xs font-medium transition-colors"
                >
                  <TrendingUp className="size-3" /> View all insights
                </Link>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <TeamSummary />
        <ActiveSessions />
      </div>

      <QuickActions />

      {/* Admin row */}
      {user?.role === "admin" && (
        <div>
          <h2 className="font-display text-foreground mb-3 text-base font-semibold">
            Admin actions
          </h2>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            <AdminTile
              icon={Star}
              label="Response ratings"
              description="View and manage ratings"
              href={ROUTES.ADMIN_RATINGS}
            />
            <AdminTile
              icon={List}
              label="All conversations"
              description="Inspect any user's chats"
              href={ROUTES.ADMIN_CONVERSATIONS}
            />
          </div>
        </div>
      )}
    </div>
  );
}

function SearchHint() {
  return (
    <div className="border-foreground/15 bg-background hidden items-center gap-2 rounded-full border px-3 py-1.5 text-xs sm:inline-flex">
      <Search className="text-foreground/45 h-3.5 w-3.5" />
      <span className="text-foreground/55">Search</span>
      <kbd className="border-foreground/15 bg-card text-foreground/65 rounded-md border px-1.5 py-0.5 font-mono text-[10px]">
        ⌘K
      </kbd>
    </div>
  );
}

function AdminTile({
  icon: Icon,
  label,
  description,
  href,
}: {
  icon: typeof Star;
  label: string;
  description: string;
  href: string;
}) {
  return (
    <Link
      href={href}
      className="lift border-border hover:border-foreground/30 bg-card flex items-center gap-3 rounded-2xl border p-4 transition-colors"
    >
      <span className="bg-foreground/8 text-foreground flex h-9 w-9 items-center justify-center rounded-full">
        <Icon className="h-4 w-4" />
      </span>
      <div className="flex-1">
        <p className="text-foreground text-sm font-semibold">{label}</p>
        <p className="text-foreground/55 text-xs">{description}</p>
      </div>
    </Link>
  );
}
