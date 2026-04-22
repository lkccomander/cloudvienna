import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { useI18n } from "../../app/providers/I18nProvider";
import { Panel } from "../../components/Panel";
import { LoadingBlock } from "../../components/feedback/LoadingBlock";
import { DataTable } from "../../components/DataTable";
import { useAuth } from "../../app/providers/AuthProvider";
import { api, ApiError } from "../../lib/api/client";
import type { Location, StudentDetail, StudentFollowupRoadmap } from "../../lib/api/types";
import { formatBoolean, formatDate, formatDateTime } from "../../lib/utils";

const stageStatusPalette = {
  completed: {
    border: "#7ca43a",
    background: "rgba(124, 164, 58, 0.18)",
    text: "#dff4b7",
    accent: "#c8ec82",
    badge: "rgba(200, 236, 130, 0.12)",
  },
  current: {
    border: "#c98829",
    background: "rgba(201, 136, 41, 0.18)",
    text: "#ffe0b6",
    accent: "#ffd58f",
    badge: "rgba(255, 213, 143, 0.12)",
  },
  pending: {
    border: "#5b76d6",
    background: "rgba(91, 118, 214, 0.18)",
    text: "#d6e0ff",
    accent: "#b6c8ff",
    badge: "rgba(182, 200, 255, 0.12)",
  },
} as const;

const emptyFollowupForm = {
  call_date: "",
  points_of_interest: "",
  main_reason: "",
  goals: "",
  notes: "",
};

function getFocusedStageNumber(followup: StudentFollowupRoadmap | null) {
  if (!followup) return 1;
  const currentStage = followup.stages.find((stage) => stage.status === "current");
  if (currentStage) return currentStage.stage_number;
  if (followup.current_stage) return followup.current_stage;
  const nextPendingStage = followup.stages.find((stage) => stage.status === "pending");
  if (nextPendingStage) return nextPendingStage.stage_number;
  return followup.stages[followup.stages.length - 1]?.stage_number ?? 1;
}

export function StudentDetailPage() {
  const { t } = useI18n();
  const { token } = useAuth();
  const params = useParams<{ studentId: string }>();
  const studentId = Number(params.studentId);
  const [student, setStudent] = useState<StudentDetail | null>(null);
  const [locations, setLocations] = useState<Location[]>([]);
  const [followup, setFollowup] = useState<StudentFollowupRoadmap | null>(null);
  const [selectedStageNumber, setSelectedStageNumber] = useState(1);
  const [followupForm, setFollowupForm] = useState(emptyFollowupForm);
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

  useEffect(() => {
    setSelectedStageNumber(getFocusedStageNumber(followup));
  }, [followup]);

  useEffect(() => {
    const selectedFollowup = followup?.followups.find((entry) => entry.stage_number === selectedStageNumber);
    setFollowupForm(
      selectedFollowup
        ? {
            call_date: selectedFollowup.call_date || "",
            points_of_interest: selectedFollowup.points_of_interest || "",
            main_reason: selectedFollowup.main_reason || "",
            goals: selectedFollowup.goals || "",
            notes: selectedFollowup.notes || "",
          }
        : emptyFollowupForm,
    );
  }, [followup, selectedStageNumber]);

  if (loading || !student) return <LoadingBlock label={t("student.detail_loading")} />;

  const summaryCards = [
    { label: t("common.location"), value: student.location || "-" },
    { label: t("common.birthday"), value: formatDate(student.birthday) },
    { label: t("common.newsletter"), value: formatBoolean(student.newsletter_opt_in) },
    { label: t("common.minor"), value: formatBoolean(student.is_minor) },
  ];
  const stageRangeLabels: Record<number, string> = {
    1: t("student.followup_range_1"),
    2: t("student.followup_range_2"),
    3: t("student.followup_range_3"),
    4: t("student.followup_range_4"),
    5: t("student.followup_range_5"),
  };

  return (
    <div className="space-y-4">
      <section className="grid gap-3 lg:grid-cols-[1.2fr_0.8fr_0.8fr]">
        <div className="glass-panel rounded-[1.75rem] px-5 py-5">
          <p className="theme-kicker">{t("student.record")}</p>
          <div className="mt-3 flex flex-wrap items-start justify-between gap-4">
            <div>
              <h1 className="theme-title text-2xl font-semibold text-[var(--text-strong)]">
                {student.name || t("student.detail_fallback")}
              </h1>
              <p className="mt-1 text-sm text-[var(--muted)]">
                ID {student.id} - {t("common.created")} {formatDateTime(student.created_at)}
              </p>
            </div>
            <div className="rounded-[1rem] border border-[var(--line)] bg-[var(--panel-soft)] px-4 py-3 text-right">
              <p className="theme-kicker">{t("common.status")}</p>
              <p
                className={`mt-2 text-sm font-semibold ${
                  student.active ? "text-status-positive" : "text-status-negative"
                }`}
              >
                {student.active ? t("student.status_record_active") : t("student.status_record_inactive")}
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
          title={t("student.identity_title")}
          subtitle={t("student.identity_subtitle")}
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
                setMessage(t("student.updated_success"));
                await load();
              } catch (error) {
                setMessage(error instanceof ApiError ? error.message : t("student.updated_failed"));
              } finally {
                setSaving(false);
              }
            }}
          >
            {[
              [t("common.name"), "name"],
              [t("common.email"), "email"],
              [t("student.field.belt"), "belt"],
              [t("common.phone"), "phone"],
              [t("student.field.phone2"), "phone2"],
              [t("common.address"), "direction"],
              [t("common.postal_code"), "postalcode"],
              [t("common.country"), "country"],
              [t("student.field.tax_id"), "taxid"],
              [t("student.field.guardian_name"), "guardian_name"],
              [t("student.field.guardian_email"), "guardian_email"],
              [t("student.field.guardian_phone"), "guardian_phone"],
              [t("student.field.guardian_phone2"), "guardian_phone2"],
              [t("student.field.guardian_relationship"), "guardian_relationship"],
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
              <span className="mb-2 block text-sm text-[var(--muted)]">{t("common.birthday")}</span>
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
              <span className="mb-2 block text-sm text-[var(--muted)]">{t("common.weight")}</span>
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
              <span className="mb-2 block text-sm text-[var(--muted)]">{t("common.location")}</span>
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
                <option value="">{t("student.no_location")}</option>
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
                {t("student.newsletter_opt_in")}
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
                {t("common.minor")}
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
                {t("student.active_label")}
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
                {saving ? t("common.saving") : t("common.save_changes")}
              </button>
              <div className="rounded-2xl border border-[var(--line)] bg-[var(--panel-soft)] px-4 py-3 text-sm text-[var(--muted)]">
                {t("student.last_refresh_snapshot")}
              </div>
            </div>
          </form>
        </Panel>

        <Panel
          title={t("student.followup_title")}
          subtitle={t("student.followup_subtitle")}
        >
          {followup ? (
            <div className="space-y-4">
              <div className="rounded-[1.2rem] border border-[#c98829] bg-[rgba(201,136,41,0.14)] px-4 py-4">
                <div className="flex items-start gap-3">
                  <div
                    className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-sm font-bold"
                    style={{ color: "#ffd58f", background: "rgba(255, 213, 143, 0.14)" }}
                    aria-hidden="true"
                  >
                    !
                  </div>
                  <div>
                    <p className="theme-kicker" style={{ color: "#ffd58f" }}>
                      {t("student.followup_warning_title")}
                    </p>
                    <p className="mt-2 text-sm text-[#ffe0b6]">{t("student.followup_warning_body")}</p>
                  </div>
                </div>
              </div>
              <div className="grid gap-3 sm:grid-cols-3">
                <div className="rounded-[1rem] border border-[var(--line)] bg-[var(--panel)] px-4 py-4">
                  <p className="theme-kicker">{t("common.current_stage")}</p>
                  <p className="theme-title mt-2 text-2xl font-semibold text-[var(--text-strong)] [font-variant-numeric:tabular-nums]">
                    {followup.current_stage ?? "-"}
                  </p>
                </div>
                <div className="rounded-[1rem] border border-[var(--line)] bg-[var(--panel)] px-4 py-4">
                  <p className="theme-kicker">{t("common.program_completed")}</p>
                  <p className="theme-title mt-2 text-2xl font-semibold text-[var(--text-strong)]">
                    {followup.program_completed ? t("common.yes") : t("common.no")}
                  </p>
                </div>
                <div className="rounded-[1rem] border border-[var(--line)] bg-[var(--panel)] px-4 py-4">
                  <p className="theme-kicker">{t("common.last_call")}</p>
                  <p className="theme-title mt-2 text-2xl font-semibold text-[var(--text-strong)]">
                    {formatDate(followup.last_call_date)}
                  </p>
                </div>
              </div>
              <div className="grid gap-3 sm:grid-cols-5">
                {followup.stages.map((stage) => {
                  const palette = stageStatusPalette[stage.status];
                  const isSelected = stage.stage_number === selectedStageNumber;
                  const statusLabel =
                    stage.status === "completed"
                      ? t("student.followup_status_completed")
                      : stage.status === "current"
                        ? t("student.followup_status_current")
                        : t("student.followup_status_pending");

                  return (
                    <button
                      key={stage.stage_number}
                      type="button"
                      onClick={() => setSelectedStageNumber(stage.stage_number)}
                      className="rounded-[1.35rem] border px-4 py-4 text-left transition duration-200 hover:-translate-y-0.5"
                      style={{
                        borderColor: palette.border,
                        background: palette.background,
                        boxShadow: isSelected ? `0 0 0 1px ${palette.accent}, 0 14px 34px rgba(15, 23, 42, 0.24)` : undefined,
                      }}
                      aria-pressed={isSelected}
                    >
                      <div>
                        <p className="theme-kicker" style={{ color: palette.accent }}>
                          {t("common.stage")}
                        </p>
                        <p className="theme-title mt-2 text-2xl font-semibold" style={{ color: palette.text }}>
                          {stage.stage_number}
                        </p>
                        <p className="mt-2 text-xs font-medium tracking-[0.08em]" style={{ color: palette.accent }}>
                          {stageRangeLabels[stage.stage_number] || t("student.followup_range_custom")}
                        </p>
                        <span
                          className="mt-3 inline-flex rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em]"
                          style={{ color: palette.accent, background: palette.badge }}
                        >
                          {statusLabel}
                        </span>
                      </div>
                      <p className="mt-4 text-sm font-medium" style={{ color: palette.text }}>
                        {stage.call_date
                          ? t("student.followup_call_logged").replace("{date}", formatDate(stage.call_date))
                          : t("student.followup_waiting")}
                      </p>
                    </button>
                  );
                })}
              </div>
              <form
                className="grid gap-4 md:grid-cols-2"
                onSubmit={async (event) => {
                  event.preventDefault();
                  if (!token) return;
                  setFollowupMessage(null);
                  try {
                    await api.upsertStudentFollowup(token, student.id, {
                      stage_number: selectedStageNumber,
                      call_date: followupForm.call_date || null,
                      points_of_interest: followupForm.points_of_interest || null,
                      main_reason: followupForm.main_reason || null,
                      goals: followupForm.goals || null,
                      notes: followupForm.notes || null,
                    });
                    await load();
                    setFollowupMessage(t("student.followup_saved"));
                  } catch (error) {
                    setFollowupMessage(error instanceof ApiError ? error.message : t("student.followup_failed"));
                  }
                }}
              >
                <label className="block">
                  <span className="mb-2 block text-sm text-[var(--muted)]">{t("common.stage")}</span>
                  <select
                    name="stage_number"
                    className="theme-select"
                    value={selectedStageNumber}
                    onChange={(event) => setSelectedStageNumber(Number(event.target.value))}
                  >
                    {Array.from({ length: 7 }).map((_, index) => (
                      <option key={index + 1} value={index + 1}>
                        {t("common.stage")} {index + 1}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="block">
                  <span className="mb-2 block text-sm text-[var(--muted)]">{t("common.last_call")}</span>
                  <input
                    name="call_date"
                    type="date"
                    className="theme-input"
                    value={followupForm.call_date}
                    onChange={(event) =>
                      setFollowupForm((current) => ({ ...current, call_date: event.target.value }))
                    }
                  />
                </label>
                <label className="block">
                  <span className="mb-2 block text-sm text-[var(--muted)]">{t("student.followup_points")}</span>
                  <input
                    name="points_of_interest"
                    className="theme-input"
                    value={followupForm.points_of_interest}
                    onChange={(event) =>
                      setFollowupForm((current) => ({ ...current, points_of_interest: event.target.value }))
                    }
                  />
                </label>
                <label className="block">
                  <span className="mb-2 block text-sm text-[var(--muted)]">{t("student.followup_main_reason")}</span>
                  <input
                    name="main_reason"
                    className="theme-input"
                    value={followupForm.main_reason}
                    onChange={(event) =>
                      setFollowupForm((current) => ({ ...current, main_reason: event.target.value }))
                    }
                  />
                </label>
                <label className="block md:col-span-2">
                  <span className="mb-2 block text-sm text-[var(--muted)]">{t("common.goals")}</span>
                  <textarea
                    name="goals"
                    rows={3}
                    className="theme-textarea"
                    value={followupForm.goals}
                    onChange={(event) =>
                      setFollowupForm((current) => ({ ...current, goals: event.target.value }))
                    }
                  />
                </label>
                <label className="block md:col-span-2">
                  <span className="mb-2 block text-sm text-[var(--muted)]">{t("common.notes")}</span>
                  <textarea
                    name="notes"
                    rows={4}
                    className="theme-textarea"
                    value={followupForm.notes}
                    onChange={(event) =>
                      setFollowupForm((current) => ({ ...current, notes: event.target.value }))
                    }
                  />
                </label>
                {followupMessage ? (
                  <div className="md:col-span-2 rounded-2xl border border-[var(--line)] bg-[var(--panel-soft)] px-4 py-3 text-sm text-[var(--text)]">
                    {followupMessage}
                  </div>
                ) : null}
                <div className="md:col-span-2">
                  <button type="submit" className="theme-primary-button px-4 py-3">
                    {t("common.save")}
                  </button>
                </div>
              </form>
              <DataTable
                columns={[
                  { key: "stage", title: t("common.stage"), render: (row) => row.stage_number },
                  { key: "call", title: t("common.last_call"), render: (row) => formatDate(row.call_date) },
                  { key: "reason", title: t("common.reason"), render: (row) => row.main_reason || "-" },
                  { key: "goals", title: t("common.goals"), render: (row) => row.goals || "-" },
                  { key: "updated", title: t("common.updated"), render: (row) => formatDateTime(row.updated_at || row.created_at) },
                ]}
                rows={followup.followups}
                rowKey={(row) => row.id}
                emptyMessage={t("student.followup_empty")}
              />
            </div>
          ) : (
            <div className="rounded-[1rem] border border-[var(--line)] bg-[var(--panel-soft)] px-4 py-5 text-sm text-[var(--muted)]">
              {t("student.followup_no_roadmap")}
            </div>
          )}
        </Panel>
      </div>

      <Panel title={t("student.summary_title")} subtitle={t("student.summary_subtitle")}>
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
