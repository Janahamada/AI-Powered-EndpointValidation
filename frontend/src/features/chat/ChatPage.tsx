import { useRef, useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Send, Sparkles, Bot, UserRound, Loader2, WifiOff, BookMarked } from "lucide-react";
import { PageHeader } from "@/components/common";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { RecommendationCard } from "@/components/RecommendationCard";
import { StatusBadge } from "@/components/StatusBadge";
import { sendChat } from "@/lib/endpoints-api";
import { apiErrorMessage } from "@/lib/api";
import { useAiStatus } from "@/hooks/queries";
import type { ChatResponse, ChatSource, ValidationStatus } from "@/types/api";

interface Message {
  role: "user" | "assistant";
  text: string;
  response?: ChatResponse;
  error?: boolean;
}

const SUGGESTIONS = [
  "What is our overall compliance posture?",
  "How many endpoints are not encrypted with BitLocker?",
  "Which endpoints are failing?",
  "What does the blueprint require for firewall?",
  "Why does tamper protection matter?",
  "Is 10.100.164.29 compliant and why?",
];

export function ChatPage() {
  const { data: aiStatus } = useAiStatus();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  async function submit(text: string) {
    const trimmed = text.trim();
    if (!trimmed || loading) return;
    setMessages((m) => [...m, { role: "user", text: trimmed }]);
    setInput("");
    setLoading(true);
    try {
      const res = await sendChat(trimmed);
      setMessages((m) => [...m, { role: "assistant", text: res.message, response: res }]);
    } catch (err) {
      setMessages((m) => [
        ...m,
        { role: "assistant", text: apiErrorMessage(err, "The assistant failed to respond."), error: true },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex h-[calc(100vh-7rem)] flex-col">
      <PageHeader
        title="AI Assistant"
        description="Ask about endpoints, the fleet, controls, or policies. Every answer is grounded in this system's data and cites its sources — never invented."
      />

      {aiStatus && !aiStatus.ollama_online && (
        <div className="mb-3 flex items-center gap-2 rounded-md border border-warning/30 bg-warning/10 px-3 py-2 text-sm text-warning">
          <WifiOff className="size-4 shrink-0" />
          LLM narrative layer offline — answers still work from the deterministic engine.
        </div>
      )}

      <Card className="flex min-h-0 flex-1 flex-col">
        <div ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto p-4">
          {messages.length === 0 && (
            <div className="flex h-full flex-col items-center justify-center gap-4 text-center">
              <div className="flex size-12 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                <Sparkles className="size-6" />
              </div>
              <div>
                <div className="font-medium">Ask about your security posture</div>
                <div className="mt-1 text-sm text-muted-foreground">
                  Fleet metrics, endpoint checks, control policies — try one:
                </div>
              </div>
              <div className="flex max-w-2xl flex-wrap justify-center gap-2">
                {SUGGESTIONS.map((s) => (
                  <button
                    key={s}
                    onClick={() => submit(s)}
                    className="rounded-full border px-4 py-1.5 text-sm text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((m, i) => (
            <ChatBubble key={i} message={m} />
          ))}

          {loading && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Bot className="size-5" />
              <Loader2 className="size-4 animate-spin" /> Thinking…
            </div>
          )}
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            submit(input);
          }}
          className="flex items-center gap-2 border-t p-3"
        >
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask anything — e.g. how many endpoints fail BitLocker?"
            disabled={loading}
          />
          <Button type="submit" size="icon" disabled={loading || !input.trim()}>
            <Send className="size-4" />
          </Button>
        </form>
      </Card>
    </div>
  );
}

function ChatBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";
  const res = message.response;
  return (
    <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : ""}`}>
      <div
        className={`flex size-8 shrink-0 items-center justify-center rounded-full ${
          isUser ? "bg-primary text-primary-foreground" : "bg-secondary text-secondary-foreground"
        }`}
      >
        {isUser ? <UserRound className="size-4" /> : <Bot className="size-4" />}
      </div>
      <div className={`min-w-0 max-w-[85%] ${isUser ? "text-right" : ""}`}>
        <div
          className={`inline-block whitespace-pre-wrap rounded-2xl px-4 py-2.5 text-left text-sm ${
            isUser
              ? "bg-primary text-primary-foreground"
              : message.error
                ? "border border-fail/30 bg-fail/10 text-fail"
                : "bg-muted"
          }`}
        >
          {message.text}
        </div>

        {res && !isUser && (
          <div className="mt-2 space-y-2 text-left">
            {/* Tabular list results */}
            {res.table.length > 0 && <ResultTable rows={res.table} />}

            {/* AI narrative summary (LLM), when present */}
            {res.ai_summary && (
              <p className="whitespace-pre-wrap rounded-md border border-primary/25 bg-primary/5 p-2 text-xs leading-relaxed">
                <span className="mr-1 font-semibold text-primary">AI summary:</span>
                {res.ai_summary}
              </p>
            )}

            {/* Grounded recommendations */}
            {res.recommendations.length > 0 && (
              <div className="space-y-2 rounded-xl border bg-card/50 p-3">
                <div className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  {res.recommendations.length} grounded recommendation
                  {res.recommendations.length === 1 ? "" : "s"}
                </div>
                {res.recommendations.map((rec, i) => (
                  <RecommendationCard key={`${rec.field}-${i}`} rec={rec} index={i + 1} />
                ))}
              </div>
            )}

            {/* Sources — how the answer was derived */}
            {res.sources.length > 0 && <SourceChips sources={res.sources} />}
          </div>
        )}
      </div>
    </div>
  );
}

function SourceChips({ sources }: { sources: ChatSource[] }) {
  return (
    <div className="flex flex-wrap items-center gap-1.5">
      <span className="flex items-center gap-1 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
        <BookMarked className="size-3" /> Sources
      </span>
      {sources.map((s, i) => (
        <span
          key={i}
          className="inline-flex items-center gap-1 rounded-md border border-border bg-muted px-2 py-0.5 text-[11px] text-muted-foreground"
          title={s.kind}
        >
          {s.label}
        </span>
      ))}
    </div>
  );
}

function ResultTable({ rows }: { rows: { hostname: string | null; values: Record<string, unknown> }[] }) {
  const cols = Object.keys(rows[0]?.values ?? {});
  return (
    <div className="overflow-x-auto rounded-lg border">
      <table className="w-full text-left text-xs">
        <thead className="bg-muted/60 text-muted-foreground">
          <tr>
            <th className="px-2.5 py-1.5 font-medium">Hostname</th>
            {cols.map((c) => (
              <th key={c} className="px-2.5 py-1.5 font-medium capitalize">
                {c.replace(/_/g, " ")}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.slice(0, 25).map((r, i) => (
            <tr key={i} className="border-t">
              <td className="px-2.5 py-1.5 font-medium">
                {r.hostname ? (
                  <Link
                    to={`/endpoints/${encodeURIComponent(r.hostname)}`}
                    className="text-primary hover:underline"
                  >
                    {r.hostname}
                  </Link>
                ) : (
                  "—"
                )}
              </td>
              {cols.map((c) => (
                <td key={c} className="px-2.5 py-1.5">
                  {c.endsWith("status") ? (
                    <StatusBadge status={String(r.values[c]) as ValidationStatus} showIcon={false} />
                  ) : (
                    String(r.values[c] ?? "—")
                  )}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {rows.length > 25 && (
        <div className="border-t px-2.5 py-1.5 text-[11px] text-muted-foreground">
          Showing 25 of {rows.length}. Use the Endpoints page to see all.
        </div>
      )}
    </div>
  );
}
