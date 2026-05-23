import { LoadingBlock } from "../../components/feedback/LoadingBlock";
import { useAuth } from "../../app/providers/AuthProvider";
import { SchedulePageContent } from "./schedule/SchedulePageContent";
import { useSchedulePage } from "./schedule/useSchedulePage";

export function SchedulePage() {
  const { token } = useAuth();
  const schedule = useSchedulePage(token);

  if (schedule.loading) return <LoadingBlock label="Loading schedule..." />;

  return <SchedulePageContent schedule={schedule} />;
}
