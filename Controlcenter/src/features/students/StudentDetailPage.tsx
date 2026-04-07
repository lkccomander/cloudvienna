import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Panel } from "../../components/Panel";
import { LoadingBlock } from "../../components/feedback/LoadingBlock";
import { DataTable } from "../../components/DataTable";
import { useAuth } from "../../app/providers/AuthProvider";
import { api, ApiError } from "../../lib/api/client";
import type { Location, StudentDetail, StudentFollowupRoadmap } from "../../lib/api/types";
import { formatBoolean, formatDate, formatDateTime } from "../../lib/utils";

export function StudentDetailPage() {
  const { token } = useAuth();
  const params = useParams<{ studentId: string }>();
  const studentId = Number(params.studentId);
  const [student, setStudent] = useState<StudentDetail | null>(null);
  const [locations, setLocations] = useState<Location[]>([]);
  const [followup, setFollowup] = useState<StudentFollowupRoadmap | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [followupMessage, setFollowupMessage] = useState<string | null>(null);

  async function load() {
    if (!token || Number.isNaN(studentId)) return;
    setLoading(true);
    try {
      const [studentData, locationsData, followupData] = await Promise.all([
        api.getStudent(token, studentId),
        api.listLocations(token),
        api.getStudentFollowups(token, studentId),
      ]);
      setStudent(studentData);
      setLocations(locationsData);
      setFollowup(followupData);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, [token, studentId]);

  if (loading || !student) return <LoadingBlock label="Loading student detail..." />;

  const summaryCards = [
    { label: "Location", value: student.location || "-" },
    { label: "Birthday", value: formatDate(student.birthday) },
    { label: "Newsletter", value: formatBoolean(student.newsletter_opt_in) },
    { label: "Minor", value: formatBoolean(student.is_minor) },
  ];

  return (
    <div className="space-y-4">
      <section className="grid gap-3 lg:grid-cols-[1.2fr_0.8fr_0.8fr]">
        <div className="glass-panel rounded-[1.75rem] px-5 py-5">
          <p className="theme-kicker">Student record</p>
          <div className="mt-3 flex flex-wrap items-start justify-between gap-4">
            <div>
              <h1 className="theme-title text-2xl font-semibold text-[var(--text-strong)]">
                {student.name || "Student detail"}
              </h1>
              <p className="mt-1 text-sm text-[var(--muted)]">
                ID {student.id} - Created {formatDateTime(student.created_at)}
              </p>
            </div>
            <div className="rounded-[1rem] border border-[var(--line)] bg-[var(--panel-soft)] px-4 py-3 text-right">
              <p className="theme-kicker">Status</p>
              <p
                className={`mt-2 text-sm font-semibold ${
                  student.active ? "text-status-positive" : "text-status-negative"
                }`}
              >
                {student.active ? "Active record" : "Inactive record"}
              </p>
            </div>
          </div>
        </div>
        {summaryCards.slice(0, 2).map((card) => (
          <div key={card.label} className="glass-panel rounded-[1.4rem] px-4 py-4">
            <p className="theme-kicker">{card.label}</p>
            <p className="theme-title mt-2 text-lg font-semibold text-[var(--text-strong)]">
              {card.value}
            </p>
          </div>
        ))}
      </section>

      <div className="grid gap-4 xl:grid-cols-[1fr_0.95fr]">
        <Panel
          title="Identity and contact"
          subtitle="Operational record fields used by reception, compliance and follow-up staff."
        >
          <form
            className="grid gap-4 md:grid-cols-2"
            onSubmit={async (event) => {
              event.preventDefault();
              if (!token) return;
              setSaving(true);
              setMessage(null);
              try {
                await api.updateStudent(token, student.id, {
                  name: student.name,
                  sex: student.sex || "NA",
                  email: student.email,
                  direction: student.direction,
                  postalcode: student.postalcode,
                  belt: student.belt,
                  phone: student.phone,
                  phone2: student.phone2,
                  weight: student.weight,
                  country: student.country,
                  taxid: student.taxid,
                  birthday: student.birthday,
                  location_id: student.location_id,
                  newsletter_opt_in: student.newsletter_opt_in ?? true,
                  is_minor: student.is_minor ?? false,
                  guardian_name: student.guardian_name,
                  guardian_email: student.guardian_email,
                  guardian_phone: student.guardian_phone,
                  guardian_phone2: student.guardian_phone2,
                  guardian_relationship: student.guardian_relationship,
                });
                setMessage("Student updated.");
                await load();
              } catch (error) {
                setMessage(error instanceof ApiError ? error.message : "Student update failed");
              } finally {
                setSaving(false);
              }
            }}
          >
            {[
              ["Name", "name"],
              ["Email", "email"],
              ["Belt", "belt"],
              ["Phone", "phone"],
              ["Phone 2", "phone2"],
              ["Address", "direction"],
              ["Postal code", "postalcode"],
              ["Country", "country"],
              ["Tax ID", "taxid"],
              ["Guardian name", "guardian_name"],
              ["Guardian email", "guardian_email"],
              ["Guardian phone", "guardian_phone"],
              ["Guardian phone 2", "guardian_phone2"],
              ["Guardian relationship", "guardian_relationship"],
            ].map(([label, key]) => (
              <label key={key} className="block">
                <span className="mb-2 block text-sm text-[var(--muted)]">{label}</span>
                <input
                  value={
                    ((student as unknown as Record<string, string | null | undefined>)[key] ?? "") as string
                  }
                  onChange={(event) =>
                    setStudent((current) =>
                      current ? ({ ...current, [key]: event.target.value } as StudentDetail) : current,
                    )
                  }
                  className="theme-input"
                />
              </label>
            ))}
            <label className="block">
              <span className="mb-2 block text-sm text-[var(--muted)]">Birthday</span>
              <input
                type="date"
                value={student.birthday || ""}
                onChange={(event) =>
                  setStudent((current) =>
                    current ? { ...current, birthday: event.target.value || null } : current,
                  )
                }
                className="theme-input"
              />
            </label>
            <label className="block">
              <span className="mb-2 block text-sm text-[var(--muted)]">Weight</span>
              <input
                value={student.weight ?? ""}
                onChange={(event) =>
                  setStudent((current) =>
                    current
                      ? {
                          ...current,
                          weight: event.target.value === "" ? null : Number(event.target.value),
                        }
                      : current,
                  )
                }
                className="theme-input"
              />
            </label>
            <label className="block">
              <span className="mb-2 block text-sm text-[var(--muted)]">Location</span>
              <select
                value={student.location_id || ""}
                onChange={(event) =>
                  setStudent((current) =>
                    current
                      ? {
                          ...current,
                          location_id: event.target.value ? Number(event.target.value) : null,
                        }
                      : current,
                  )
                }
                className="theme-select"
              >
                <option value="">No location</option>
                {locations.map((location) => (
                  <option key={location.id} value={location.id}>
                    {location.name}
                  </option>
                ))}
              </select>
            </label>
            <div className="md:col-span-2 grid gap-3 md:grid-cols-3">
              <label className="theme-check text-sm">
                <input
                  type="checkbox"
                  checked={student.newsletter_opt_in ?? false}
                  onChange={(event) =>
                    setStudent((current) =>
                      current ? { ...current, newsletter_opt_in: event.target.checked } : current,
                    )
                  }
                />
                Newsletter opt-in
              </label>
              <label className="theme-check text-sm">
                <input
                  type="checkbox"
                  checked={student.is_minor ?? false}
                  onChange={(event) =>
                    setStudent((current) =>
                      current ? { ...current, is_minor: event.target.checked } : current,
                    )
                  }
                />
                Minor
              </label>
              <label className="theme-check text-sm">
                <input
                  type="checkbox"
                  checked={student.active ?? false}
                  onChange={async (event) => {
                    if (!token) return;
                    await api.setStudentActive(token, student.id, event.target.checked);
                    await load();
                  }}
                />
                Active
              </label>
            </div>
            {message ? (
              <div className="md:col-span-2 rounded-2xl border border-[var(--line)] bg-[var(--panel-soft)] px-4 py-3 text-sm text-[var(--text)]">
                {message}
              </div>
            ) : null}
            <div className="md:col-span-2 flex flex-wrap gap-3">
              <button
                type="submit"
                disabled={saving}
                className="theme-primary-button px-4 py-3 disabled:opacity-70"
              >
                {saving ? "Saving..." : "Save student"}
              </button>
              <div className="rounded-2xl border border-[var(--line)] bg-[var(--panel-soft)] px-4 py-3 text-sm text-[var(--muted)]">
                Last refresh from record snapshot
              </div>
            </div>
          </form>
        </Panel>

        <Panel
          title="Follow-up roadmap"
          subtitle="Call stages and coaching signals tied to the academy follow-up process."
        >
          {followup ? (
            <div className="space-y-4">
              <div className="grid gap-3 sm:grid-cols-3">
                <div className="rounded-[1rem] border border-[var(--line)] bg-[var(--panel)] px-4 py-4">
                  <p className="theme-kicker">Current stage</p>
                  <p className="theme-title mt-2 text-2xl font-semibold text-[var(--text-strong)] [font-variant-numeric:tabular-nums]">
                    {followup.current_stage ?? "-"}
                  </p>
                </div>
                <div className="rounded-[1rem] border border-[var(--line)] bg-[var(--panel)] px-4 py-4">
                  <p className="theme-kicker">Program completed</p>
                  <p className="theme-title mt-2 text-2xl font-semibold text-[var(--text-strong)]">
                    {followup.program_completed ? "Yes" : "No"}
                  </p>
                </div>
                <div className="rounded-[1rem] border border-[var(--line)] bg-[var(--panel)] px-4 py-4">
                  <p className="theme-kicker">Last call</p>
                  <p className="theme-title mt-2 text-2xl font-semibold text-[var(--text-strong)]">
                    {formatDate(followup.last_call_date)}
                  </p>
                </div>
              </div>
              <div className="grid gap-3 sm:grid-cols-5">
                {followup.stages.map((stage) => {
                  const stageClass =
                    stage.status === "completed"
                      ? "border-[var(--line)] bg-[color:var(--success)]/10"
                      : stage.status === "current"
                        ? "border-[var(--accent)]/50 bg-[var(--accent-soft)]"
                        : "border-[var(--line)] bg-[var(--panel-soft)]";

                  return (
                    <div key={stage.stage_number} className={`rounded-[1rem] border px-4 py-4 text-center ${stageClass}`}>
                      <p className="theme-kicker">Stage</p>
                      <p className="theme-title mt-2 text-2xl font-semibold text-[var(--text-strong)]">
                        {stage.stage_number}
                      </p>
                      <p className="mt-2 text-sm text-[var(--text)]">{stage.status}</p>
                    </div>
                  );
                })}
              </div>
              <form
                className="grid gap-4 md:grid-cols-2"
                onSubmit={async (event) => {
                  event.preventDefault();
                  if (!token) return;
                  const formData = new FormData(event.currentTarget);
                  setFollowupMessage(null);
                  try {
                    await api.upsertStudentFollowup(token, student.id, {
                      stage_number: Number(formData.get("stage_number")),
                      call_date: formData.get("call_date") || null,
                      points_of_interest: formData.get("points_of_interest") || null,
                      main_reason: formData.get("main_reason") || null,
                      goals: formData.get("goals") || null,
                      notes: formData.get("notes") || null,
                    });
                    await load();
                    setFollowupMessage("Follow-up saved.");
                    event.currentTarget.reset();
                  } catch (error) {
                    setFollowupMessage(error instanceof ApiError ? error.message : "Follow-up save failed");
                  }
                }}
              >
                <label className="block">
                  <span className="mb-2 block text-sm text-[var(--muted)]">Stage</span>
                  <select
                    name="stage_number"
                    className="theme-select"
                    defaultValue={followup.current_stage ?? 1}
                  >
                    {Array.from({ length: 7 }).map((_, index) => (
                      <option key={index + 1} value={index + 1}>
                        Stage {index + 1}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="block">
                  <span className="mb-2 block text-sm text-[var(--muted)]">Call date</span>
                  <input name="call_date" type="date" className="theme-input" />
                </label>
                <label className="block">
                  <span className="mb-2 block text-sm text-[var(--muted)]">Points of interest</span>
                  <input name="points_of_interest" className="theme-input" />
                </label>
                <label className="block">
                  <span className="mb-2 block text-sm text-[var(--muted)]">Main reason</span>
                  <input name="main_reason" className="theme-input" />
                </label>
                <label className="block md:col-span-2">
                  <span className="mb-2 block text-sm text-[var(--muted)]">Goals</span>
                  <textarea name="goals" rows={3} className="theme-textarea" />
                </label>
                <label className="block md:col-span-2">
                  <span className="mb-2 block text-sm text-[var(--muted)]">Notes</span>
                  <textarea name="notes" rows={4} className="theme-textarea" />
                </label>
                {followupMessage ? (
                  <div className="md:col-span-2 rounded-2xl border border-[var(--line)] bg-[var(--panel-soft)] px-4 py-3 text-sm text-[var(--text)]">
                    {followupMessage}
                  </div>
                ) : null}
                <div className="md:col-span-2">
                  <button type="submit" className="theme-primary-button px-4 py-3">
                    Save follow-up
                  </button>
                </div>
              </form>
              <DataTable
                columns={[
                  { key: "stage", title: "Stage", render: (row) => row.stage_number },
                  { key: "call", title: "Call date", render: (row) => formatDate(row.call_date) },
                  { key: "reason", title: "Reason", render: (row) => row.main_reason || "-" },
                  { key: "goals", title: "Goals", render: (row) => row.goals || "-" },
                  { key: "updated", title: "Updated", render: (row) => formatDateTime(row.updated_at || row.created_at) },
                ]}
                rows={followup.followups}
                rowKey={(row) => row.id}
                emptyMessage="No follow-up calls have been logged for this student yet."
              />
            </div>
          ) : (
            <div className="rounded-[1rem] border border-[var(--line)] bg-[var(--panel-soft)] px-4 py-5 text-sm text-[var(--muted)]">
              No roadmap data is available for this student yet.
            </div>
          )}
        </Panel>
      </div>

      <Panel title="Student summary" subtitle="High-signal identity and compliance data">
        <div className="grid gap-4 md:grid-cols-4">
          {summaryCards.map((card) => (
            <div
              key={card.label}
              className="rounded-[1rem] border border-[var(--line)] bg-[var(--panel-soft)] px-4 py-4"
            >
              <p className="theme-kicker">{card.label}</p>
              <p className="theme-title mt-2 text-lg font-semibold text-[var(--text-strong)]">
                {card.value}
              </p>
            </div>
          ))}
        </div>
      </Panel>
    </div>
  );
}
