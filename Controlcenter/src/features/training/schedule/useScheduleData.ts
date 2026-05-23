import { useEffect, useState, type Dispatch, type SetStateAction } from "react";
import { api, ApiError } from "../../../lib/api/client";
import type { ClassRow, Location, SessionRow } from "../../../lib/api/types";

type UseScheduleDataOptions = {
  onLoadError: (message: string | null) => void;
};

type UseScheduleDataResult = {
  rows: SessionRow[];
  classes: ClassRow[];
  locations: Location[];
  loading: boolean;
  setRows: Dispatch<SetStateAction<SessionRow[]>>;
  refresh: () => void;
};

export function useScheduleData(token: string | null | undefined, { onLoadError }: UseScheduleDataOptions): UseScheduleDataResult {
  const [rows, setRows] = useState<SessionRow[]>([]);
  const [classes, setClasses] = useState<ClassRow[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [refreshKey, setRefreshKey] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;
    const authToken = token;
    let ignore = false;

    async function load() {
      setLoading(true);
      try {
        const [sessionsData, classesData, locationsData] = await Promise.all([
          api.listSessions(authToken),
          api.listClasses(authToken),
          api.listLocations(authToken),
        ]);
        if (ignore) return;
        setRows(sessionsData);
        setClasses(classesData);
        setLocations(locationsData);
        onLoadError(null);
      } catch (error) {
        if (!ignore) {
          onLoadError(error instanceof ApiError ? error.message : "Schedule load failed");
        }
      } finally {
        if (!ignore) setLoading(false);
      }
    }

    void load();
    return () => {
      ignore = true;
    };
  }, [onLoadError, refreshKey, token]);

  function refresh() {
    setRefreshKey((current) => current + 1);
  }

  return {
    rows,
    classes,
    locations,
    loading,
    setRows,
    refresh,
  };
}
