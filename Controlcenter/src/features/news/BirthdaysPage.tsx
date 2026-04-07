import { useEffect, useState } from "react";
import { useI18n } from "../../app/providers/I18nProvider";
import { Panel } from "../../components/Panel";
import { LoadingBlock } from "../../components/feedback/LoadingBlock";
import { DataTable } from "../../components/DataTable";
import { useAuth } from "../../app/providers/AuthProvider";
import { api } from "../../lib/api/client";
import type { BirthdayRow } from "../../lib/api/types";
import { formatDate } from "../../lib/utils";

export function BirthdaysPage() {
  const { t } = useI18n();
  const { token } = useAuth();
  const [rows, setRows] = useState<BirthdayRow[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const run = async () => {
      if (!token) return;
      setLoading(true);
      try {
        const data = await api.newsBirthdays(token);
        if (!cancelled) setRows(data);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    void run();
    return () => {
      cancelled = true;
    };
  }, [token]);

  if (loading) return <LoadingBlock label={t("common.loading")} />;

  return (
    <Panel title={t("news.birthdays_title")} subtitle={t("news.birthdays_subtitle")}>
      <DataTable
        columns={[
          { key: "name", title: t("common.student"), render: (row) => row.name || "-" },
          { key: "belt", title: "Belt", render: (row) => row.belt || "-" },
          { key: "birthday", title: t("dashboard.birthdays"), render: (row) => formatDate(row.birthday) },
          {
            key: "active",
            title: t("common.status"),
            render: (row) => (
              <span className={row.active ? "text-status-positive" : "text-status-negative"}>
                {row.active ? t("common.active") : t("common.inactive")}
              </span>
            ),
          },
        ]}
        rows={rows}
        rowKey={(row, index) => `${row.name}-${index}`}
        emptyMessage="No birthday records are available right now."
      />
    </Panel>
  );
}
