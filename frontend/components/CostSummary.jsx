import React, { useMemo, useState } from "react";
import {
  DollarSign,
  TrendingUp,
  AlertCircle,
  Calendar,
  Beaker,
  Edit2,
  Check,
} from "lucide-react";
import { hydroIonsService } from "../../services/hydroIons";

/**
 * CostSummary (BEST)
 *
 * Back/Front integration hardening:
 * - Tolerates multiple backend shapes for costData + cost_breakdown items.
 * - Avoids runtime crashes on undefined / string numeric values.
 * - Uses consistent cost-per-liter / cost-per-m3 calculations even if only one exists.
 * - Improves acid + micronutrient detection using fertilizer_type/id when available.
 */

const toNum = (v, fallback = 0) => {
  const n = Number(v);
  return Number.isFinite(n) ? n : fallback;
};

const safeLower = (s) => (typeof s === "string" ? s.toLowerCase() : "");

const normalizeBreakdownItem = (item) => {
  if (!item || typeof item !== "object") return null;

  const fertilizer_id = item.fertilizer_id ?? item.id ?? item.fert_id ?? "";
  const fertilizer_name =
    item.fertilizer_name ?? item.name ?? item.fert_name ?? fertilizer_id;
  const fertilizer_type = (
    item.fertilizer_type ??
    item.type ??
    item.fert_type ??
    ""
  )
    .toString()
    .toLowerCase();

  // quantity/unit normalization
  // Prefer explicit quantity/unit. Otherwise derive from grams_total/ml_total if present.
  let unit = item.unit ?? item.price_unit ?? item.qty_unit ?? null;
  let quantity = item.quantity ?? item.qty ?? null;

  const grams_total = item.grams_total ?? item.grams ?? null;
  const ml_total = item.ml_total ?? item.ml ?? null;

  if (quantity === null || quantity === undefined) {
    if (ml_total !== null && ml_total !== undefined) {
      unit = unit ?? "L";
      quantity = toNum(ml_total) / 1000;
    } else if (grams_total !== null && grams_total !== undefined) {
      unit = unit ?? "kg";
      quantity = toNum(grams_total) / 1000;
    }
  }

  unit = (unit || "kg").toString();
  quantity = toNum(quantity, 0);

  const unit_cost_mxn = toNum(
    item.unit_cost_mxn ?? item.unit_cost ?? item.unit_price ?? item.price ?? 0,
    0,
  );
  const total_cost_mxn = toNum(
    item.total_cost_mxn ??
      item.total_cost ??
      item.subtotal ??
      item.cost_total ??
      0,
    0,
  );

  return {
    ...item,
    fertilizer_id,
    fertilizer_name,
    fertilizer_type,
    unit,
    quantity,
    unit_cost_mxn,
    total_cost_mxn,
    is_custom_price: Boolean(
      item.is_custom_price ?? item.custom_price ?? false,
    ),
  };
};

const inferIsAcid = (item) => {
  const t = safeLower(item?.fertilizer_type);
  if (t === "acid") return true;
  const id = safeLower(item?.fertilizer_id);
  const nm = safeLower(item?.fertilizer_name);
  return (
    id.includes("acid") ||
    nm.includes("ácido") ||
    nm.includes("acido") ||
    nm.includes("acid")
  );
};

const inferIsMicronutrient = (item) => {
  const nm = safeLower(item?.fertilizer_name);
  const id = safeLower(item?.fertilizer_id);
  const hay = `${nm} ${id}`;
  return [
    "hierro",
    "iron",
    "manganeso",
    "manganese",
    "zinc",
    "cobre",
    "copper",
    "boro",
    "boron",
    "molibdato",
    "molyb",
    "quelato",
    "chelate",
    "edta",
    "eddha",
  ].some((k) => hay.includes(k));
};

const getReservoirLiters = (sessionData) => {
  if (!sessionData || typeof sessionData !== "object") return null;
  return (
    sessionData.reservoir_volume_liters ??
    sessionData.volume_liters ??
    sessionData.reservoir_volume ??
    sessionData.reservoir_liters ??
    null
  );
};

const CostSummary = ({
  costData,
  sessionData,
  preparationMode = "direct",
  currency = null,
  showBreakdown = true,
  showProjections = true,
  editable = false,
  onPriceUpdate = null,
}) => {
  const effectiveCurrency = currency || costData?.currency || "MXN";
  const formatCurrency = (amount) => {
    if (hydroIonsService?.formatCurrency)
      return hydroIonsService.formatCurrency(amount, effectiveCurrency);
    try {
      return new Intl.NumberFormat("es-MX", {
        style: "currency",
        currency: effectiveCurrency,
      }).format(toNum(amount, 0));
    } catch {
      return `$${toNum(amount, 0).toFixed(2)}`;
    }
  };

  const [editingId, setEditingId] = useState(null);
  const [editValue, setEditValue] = useState("");

  const normalized = useMemo(() => {
    if (!costData || typeof costData !== "object") return null;

    const costBreakdownRaw =
      costData.cost_breakdown ?? costData.breakdown ?? costData.items ?? [];
    const cost_breakdown = Array.isArray(costBreakdownRaw)
      ? costBreakdownRaw.map(normalizeBreakdownItem).filter(Boolean)
      : [];

    // Keep compatibility for naming (MXN suffix may actually be user currency)
    const total_cost_mxn = toNum(
      costData.total_cost_mxn ?? costData.total_cost ?? costData.total ?? 0,
      0,
    );
    const total_fertilizer_cost_mxn = toNum(
      costData.total_fertilizer_cost_mxn ??
        costData.total_fertilizer_cost ??
        costData.fertilizers_total ??
        0,
      0,
    );
    const total_acid_cost_mxn = toNum(
      costData.total_acid_cost_mxn ??
        costData.total_acid_cost ??
        costData.acids_total ??
        0,
      0,
    );
    const cost_per_liter =
      costData.cost_per_liter !== undefined
        ? toNum(costData.cost_per_liter, 0)
        : null;
    const cost_per_m3 =
      costData.cost_per_m3 !== undefined
        ? toNum(costData.cost_per_m3, 0)
        : null;

    const costPerLiter =
      cost_per_liter ?? (cost_per_m3 !== null ? cost_per_m3 / 1000 : 0);
    const costPerM3 =
      cost_per_m3 ?? (cost_per_liter !== null ? cost_per_liter * 1000 : 0);

    return {
      ...costData,
      cost_breakdown,
      total_cost_mxn,
      total_fertilizer_cost_mxn,
      total_acid_cost_mxn,
      cost_per_liter: costPerLiter,
      cost_per_m3: costPerM3,
    };
  }, [costData]);

  if (!normalized) {
    return (
      <div className="cost-summary-empty">
        <DollarSign size={32} className="cost-summary-empty-icon" />
        <h3>No hay datos de costos</h3>
        <p>Calcula las dosis para ver el resumen de costos.</p>
      </div>
    );
  }

  const handleEditStart = (item) => {
    setEditingId(item.fertilizer_id);
    setEditValue(String(item.unit_cost_mxn ?? ""));
  };

  const handleEditSave = (item) => {
    const newPrice = toNum(editValue, NaN);
    if (Number.isFinite(newPrice) && newPrice >= 0 && onPriceUpdate) {
      // Extra arg is safe (ignored if handler only expects 2 args)
      onPriceUpdate(item.fertilizer_id, newPrice, item.unit);
    }
    setEditingId(null);
    setEditValue("");
  };

  const handleKeyDown = (e, item) => {
    if (e.key === "Enter") handleEditSave(item);
    if (e.key === "Escape") {
      setEditingId(null);
      setEditValue("");
    }
  };

  const getVolumeDescription = () => {
    if (preparationMode === "stock_ab") {
      return "Costos calculados para 100 m³ de solución final";
    }
    const reservoir = getReservoirLiters(sessionData);
    if (reservoir) {
      const liters = toNum(reservoir, 0);
      if (liters >= 1000)
        return `Costos calculados para ${(liters / 1000).toFixed(1)} m³ (${liters.toFixed(0)} L)`;
      return `Costos calculados para ${liters.toFixed(0)} L`;
    }
    return "Costos calculados por la solución propuesta";
  };

  const getReservoirLabel = () => {
    if (preparationMode === "stock_ab") return "Costo Total (100 m³)";
    const reservoir = getReservoirLiters(sessionData);
    if (reservoir) {
      const liters = toNum(reservoir, 0);
      if (liters >= 1000)
        return `Costo Total (${(liters / 1000).toFixed(1)} m³)`;
      return `Costo Total (${liters.toFixed(0)} L)`;
    }
    return "Costo Total";
  };

  // Filterable breakdown (optional UI)
  const [filter, setFilter] = useState("all");
  const filteredBreakdown = useMemo(() => {
    const items = normalized.cost_breakdown || [];
    if (filter === "all") return items;
    if (filter === "acids") return items.filter(inferIsAcid);
    if (filter === "micros") return items.filter(inferIsMicronutrient);
    if (filter === "salts")
      return items.filter((x) => !inferIsAcid(x) && !inferIsMicronutrient(x));
    return items;
  }, [normalized.cost_breakdown, filter]);

  return (
    <div className="cost-summary-container">
      <div className="cost-summary-header">
        <h3 className="cost-summary-title">Resumen de Costos</h3>
        <p className="cost-summary-subtitle">{getVolumeDescription()}</p>
      </div>

      <div className="cost-summary-cards">
        <div className="cost-card cost-card-highlight">
          <div className="cost-card-icon">
            <DollarSign size={24} />
          </div>
          <div className="cost-card-content">
            <span className="cost-card-label">{getReservoirLabel()}</span>
            <span className="cost-card-value cost-card-value-lg">
              {formatCurrency(normalized.total_cost_mxn)}
            </span>
            <span className="cost-card-subtitle">
              Incluye fertilizantes y ácidos
            </span>
          </div>
        </div>

        <div className="cost-card cost-card-outline cost-card-green">
          <div className="cost-card-header">
            <DollarSign size={16} />
            <span>Fertilizantes</span>
          </div>
          <span className="cost-card-value">
            {formatCurrency(normalized.total_fertilizer_cost_mxn)}
          </span>
        </div>

        <div className="cost-card cost-card-outline cost-card-amber">
          <div className="cost-card-header">
            <Beaker size={16} />
            <span>Ácidos</span>
          </div>
          <span className="cost-card-value">
            {formatCurrency(normalized.total_acid_cost_mxn)}
          </span>
        </div>

        <div className="cost-card cost-card-outline">
          <div className="cost-card-header">
            <TrendingUp size={16} />
            <span>Costo por m³</span>
          </div>
          <span className="cost-card-value">
            {formatCurrency(normalized.cost_per_m3)}
          </span>
        </div>
      </div>

      {showBreakdown && filteredBreakdown.length > 0 && (
        <div className="cost-breakdown-section">
          <div className="cost-breakdown-header">
            <h4>Desglose por producto</h4>
            <div className="cost-breakdown-actions">
              <select
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                className="cost-breakdown-filter"
              >
                <option value="all">Todos</option>
                <option value="salts">Sales</option>
                <option value="acids">Ácidos</option>
                <option value="micros">Micronutrientes</option>
              </select>
            </div>
          </div>

          <div className="cost-breakdown-table-desktop">
            <table>
              <thead>
                <tr>
                  <th>Producto</th>
                  <th>Cantidad</th>
                  <th>Precio unit.</th>
                  <th>Subtotal</th>
                </tr>
              </thead>
              <tbody>
                {filteredBreakdown.map((item) => {
                  const isAcid = inferIsAcid(item);
                  const isMicro = inferIsMicronutrient(item);
                  const key = item.fertilizer_id || item.fertilizer_name;
                  return (
                    <tr
                      key={key}
                      className={`${isAcid ? "acid-row" : ""} ${isMicro ? "micro-row" : ""}`}
                    >
                      <td>
                        <div className="breakdown-product">
                          {isAcid && <Beaker size={14} className="icon-acid" />}
                          {isMicro && !isAcid && <span className="dot-micro" />}
                          <span>{item.fertilizer_name}</span>
                          {item.is_custom_price && (
                            <span className="cost-card-badge">
                              PERSONALIZADO
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="mono">
                        {toNum(item.quantity).toFixed(3)} {item.unit}
                      </td>
                      <td className="mono">
                        {editable && onPriceUpdate ? (
                          editingId === item.fertilizer_id ? (
                            <div className="price-edit-container">
                              <span>$</span>
                              <input
                                type="number"
                                value={editValue}
                                onChange={(e) => setEditValue(e.target.value)}
                                onKeyDown={(e) => handleKeyDown(e, item)}
                                onBlur={() => handleEditSave(item)}
                                autoFocus
                                className="price-edit-input"
                                min="0"
                                step="0.01"
                              />
                              <button
                                onClick={() => handleEditSave(item)}
                                className="price-edit-save"
                              >
                                <Check size={14} />
                              </button>
                            </div>
                          ) : (
                            <button
                              onClick={() => handleEditStart(item)}
                              className={`price-edit-btn ${item.is_custom_price ? "custom" : ""}`}
                              title={`Editar precio por ${item.unit}`}
                            >
                              {formatCurrency(item.unit_cost_mxn || 0)}
                              <Edit2 size={12} />
                            </button>
                          )
                        ) : (
                          formatCurrency(item.unit_cost_mxn || 0)
                        )}
                      </td>
                      <td className="mono bold">
                        {formatCurrency(item.total_cost_mxn || 0)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <div className="cost-breakdown-cards-mobile">
            {filteredBreakdown.map((item) => {
              const isAcid = inferIsAcid(item);
              const isMicro = inferIsMicronutrient(item);
              const key = item.fertilizer_id || item.fertilizer_name;
              return (
                <div
                  key={key}
                  className={`breakdown-card ${isAcid ? "acid" : ""} ${isMicro ? "micro" : ""}`}
                >
                  <div className="breakdown-card-header">
                    {isAcid && <Beaker size={14} className="icon-acid" />}
                    {isMicro && !isAcid && <span className="dot-micro" />}
                    <span className="breakdown-card-name">
                      {item.fertilizer_name}
                    </span>
                    {item.is_custom_price && (
                      <span className="cost-card-badge">PERSONALIZADO</span>
                    )}
                  </div>
                  <div className="breakdown-card-details">
                    <div className="breakdown-card-row">
                      <span>Cantidad:</span>
                      <span className="mono">
                        {toNum(item.quantity).toFixed(3)} {item.unit}
                      </span>
                    </div>
                    <div className="breakdown-card-row">
                      <span>Precio unit.:</span>
                      {editable && onPriceUpdate ? (
                        editingId === item.fertilizer_id ? (
                          <div className="price-edit-container-mobile">
                            <span>$</span>
                            <input
                              type="number"
                              value={editValue}
                              onChange={(e) => setEditValue(e.target.value)}
                              onKeyDown={(e) => handleKeyDown(e, item)}
                              onBlur={() => handleEditSave(item)}
                              autoFocus
                              className="price-edit-input-mobile"
                              min="0"
                              step="0.01"
                            />
                            <button
                              onClick={() => handleEditSave(item)}
                              className="price-edit-save-mobile"
                            >
                              <Check size={14} />
                            </button>
                          </div>
                        ) : (
                          <button
                            onClick={() => handleEditStart(item)}
                            className={`price-edit-btn-mobile ${item.is_custom_price ? "custom" : ""}`}
                            title={`Editar precio por ${item.unit}`}
                          >
                            {formatCurrency(item.unit_cost_mxn || 0)}
                            <Edit2 size={12} />
                          </button>
                        )
                      ) : (
                        <span className="mono">
                          {formatCurrency(item.unit_cost_mxn || 0)}
                        </span>
                      )}
                    </div>
                    <div className="breakdown-card-row total">
                      <span>Subtotal:</span>
                      <span className="mono bold">
                        {formatCurrency(item.total_cost_mxn || 0)}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {showProjections &&
        (normalized.monthly_cost_projection_mxn ||
          normalized.cultivation_area_m2 ||
          normalized.daily_consumption_l_per_m2) && (
          <div className="cost-projection-section">
            <div className="cost-projection-card">
              <div className="cost-projection-header">
                <Calendar size={20} />
                <h4>Proyección Mensual</h4>
              </div>

              <div className="cost-projection-stats">
                <div className="cost-projection-stat">
                  <span className="stat-label">Área de cultivo</span>
                  <span className="stat-value">
                    {normalized.cultivation_area_m2
                      ? `${toNum(normalized.cultivation_area_m2).toFixed(0)} m²`
                      : "No especificada"}
                  </span>
                </div>
                <div className="cost-projection-stat">
                  <span className="stat-label">Consumo diario</span>
                  <span className="stat-value">
                    {normalized.daily_consumption_l_per_m2
                      ? `${toNum(normalized.daily_consumption_l_per_m2).toFixed(2)} L/m²`
                      : "No especificado"}
                  </span>
                </div>
              </div>

              <div className="cost-projection-total">
                <TrendingUp size={28} />
                <div>
                  <span className="projection-label">
                    Costo estimado mensual
                  </span>
                  <span className="projection-value">
                    {normalized.monthly_cost_projection_mxn !== null &&
                    normalized.monthly_cost_projection_mxn !== undefined
                      ? formatCurrency(normalized.monthly_cost_projection_mxn)
                      : "Ingresa área y consumo"}
                  </span>
                </div>
              </div>

              <div className="cost-projection-note">
                <AlertCircle size={16} />
                <p>
                  <strong>Nota:</strong> Esta proyección asume consumo constante
                  y precios estables. Los costos reales pueden variar según la
                  etapa fenológica del cultivo.
                </p>
              </div>
            </div>
          </div>
        )}

      <div className="cost-unit-cards">
        <div className="cost-unit-card">
          <span className="cost-unit-label">Costo por m³</span>
          <span className="cost-unit-value">
            {formatCurrency(normalized.cost_per_m3 || 0)}
          </span>
        </div>
        <div className="cost-unit-card">
          <span className="cost-unit-label">Costo por litro</span>
          <span className="cost-unit-value">
            {formatCurrency(normalized.cost_per_liter || 0)}
          </span>
        </div>
      </div>

      <div className="cost-summary-footer">
        <p>
          Precios capturados al momento del cálculo. Consulta con tu proveedor
          para cotizaciones actualizadas.
        </p>
      </div>

      {/* Styles: kept close to original to avoid regressions */}
      <style>{`
        .cost-summary-container {
          background: var(--color-background);
          border-radius: var(--border-radius-lg);
          box-shadow: var(--shadow-md);
          border: 1px solid var(--color-border);
          overflow: hidden;
        }

        .cost-summary-empty {
          background: var(--color-background);
          border-radius: var(--border-radius-lg);
          box-shadow: var(--shadow-md);
          border: 1px solid var(--color-border);
          padding: var(--space-8);
          text-align: center;
        }

        .cost-summary-empty-icon {
          color: var(--color-text-tertiary);
          margin-bottom: var(--space-3);
        }

        .cost-summary-header {
          padding: var(--space-5) var(--space-5);
          border-bottom: 1px solid var(--color-border);
          background: linear-gradient(135deg, var(--color-primary-light) 0%, #eaf3ed 100%);
        }

        .cost-summary-title {
          font-size: var(--text-lg);
          font-weight: var(--font-semibold);
          color: var(--color-text-primary);
          margin: 0 0 var(--space-1) 0;
        }

        .cost-summary-subtitle {
          font-size: var(--text-sm);
          color: var(--color-text-secondary);
          margin: 0;
        }

        .cost-summary-cards {
          padding: var(--space-4);
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
          gap: var(--space-3);
        }

        @media (min-width: 768px) {
          .cost-summary-cards {
            padding: var(--space-5);
            gap: var(--space-4);
          }
        }

        .cost-card {
          border-radius: var(--border-radius-md);
          padding: var(--space-4);
          display: flex;
          flex-direction: column;
          position: relative;
        }

        .cost-card-highlight {
          background: linear-gradient(135deg, #059669 0%, #047857 100%);
          color: white;
          grid-column: 1 / -1;
          flex-direction: row;
          align-items: center;
          gap: var(--space-4);
        }

        @media (min-width: 640px) {
          .cost-card-highlight {
            grid-column: auto;
          }
        }

        .cost-card-icon {
          width: 48px;
          height: 48px;
          background: rgba(255,255,255,0.2);
          border-radius: var(--border-radius-md);
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
        }

        .cost-card-content {
          display: flex;
          flex-direction: column;
        }

        .cost-card-label {
          font-size: var(--text-sm);
          opacity: 0.9;
          margin-bottom: var(--space-1);
        }

        .cost-card-value {
          font-size: 1.25rem;
          font-weight: var(--font-bold);
        }

        .cost-card-value-lg {
          font-size: 1.5rem;
        }

        @media (min-width: 768px) {
          .cost-card-value-lg {
            font-size: 1.75rem;
          }
        }

        .cost-card-subtitle {
          font-size: var(--text-xs);
          opacity: 0.8;
          margin-top: var(--space-1);
        }

        .cost-card-outline {
          background: var(--color-background);
          border: 2px solid var(--color-border);
        }

        .cost-card-green {
          border-color: var(--color-primary);
        }

        .cost-card-green .cost-card-header {
          color: var(--color-primary);
        }

        .cost-card-amber {
          border-color: #f59e0b;
        }

        .cost-card-amber .cost-card-header {
          color: #d97706;
        }

        .cost-card-header {
          display: flex;
          align-items: center;
          gap: var(--space-2);
          font-size: var(--text-sm);
          font-weight: var(--font-medium);
          margin-bottom: var(--space-2);
        }

        .cost-card-badge {
          margin-left: 8px;
          background: #fef3c7;
          color: #92400e;
          padding: 2px 6px;
          border-radius: var(--border-radius-sm);
          font-size: 0.6rem;
          font-weight: var(--font-semibold);
          letter-spacing: 0.5px;
        }

        .cost-breakdown-section {
          padding: var(--space-4);
          border-top: 1px solid var(--color-border);
        }

        @media (min-width: 768px) {
          .cost-breakdown-section {
            padding: 0 var(--space-5) var(--space-5);
          }
        }

        .cost-breakdown-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: var(--space-3);
          margin: var(--space-4) 0 var(--space-3);
        }

        .cost-breakdown-filter {
          background: var(--color-background);
          border: 1px solid var(--color-border);
          border-radius: var(--border-radius-md);
          padding: 6px 10px;
          font-size: var(--text-sm);
        }

        .cost-breakdown-table-desktop {
          display: none;
          overflow-x: auto;
          border: 1px solid var(--color-border);
          border-radius: var(--border-radius-md);
        }

        @media (min-width: 768px) {
          .cost-breakdown-table-desktop {
            display: block;
          }
        }

        table {
          width: 100%;
          border-collapse: collapse;
          font-size: var(--text-sm);
        }

        th, td {
          padding: 12px;
          text-align: left;
          border-bottom: 1px solid var(--color-border);
        }

        th {
          background: var(--color-background-secondary);
          font-weight: var(--font-semibold);
          color: var(--color-text-secondary);
        }

        .breakdown-product {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .icon-acid {
          color: #d97706;
        }

        .dot-micro {
          width: 8px;
          height: 8px;
          border-radius: 999px;
          background: #3b82f6;
          display: inline-block;
        }

        .acid-row {
          background: rgba(245, 158, 11, 0.08);
        }

        .micro-row {
          background: rgba(59, 130, 246, 0.06);
        }

        .mono {
          font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
        }

        .bold {
          font-weight: var(--font-semibold);
        }

        .price-edit-btn, .price-edit-btn-mobile {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          background: transparent;
          border: 1px solid var(--color-border);
          padding: 6px 10px;
          border-radius: var(--border-radius-md);
          cursor: pointer;
          font-size: var(--text-sm);
        }

        .price-edit-btn.custom, .price-edit-btn-mobile.custom {
          border-color: #f59e0b;
        }

        .price-edit-container, .price-edit-container-mobile {
          display: inline-flex;
          align-items: center;
          gap: 6px;
        }

        .price-edit-input, .price-edit-input-mobile {
          width: 90px;
          padding: 6px 8px;
          border: 1px solid var(--color-border);
          border-radius: var(--border-radius-md);
        }

        .price-edit-save, .price-edit-save-mobile {
          border: 0;
          background: var(--color-primary);
          color: white;
          border-radius: var(--border-radius-md);
          padding: 6px;
          cursor: pointer;
        }

        .cost-breakdown-cards-mobile {
          display: grid;
          gap: 10px;
        }

        @media (min-width: 768px) {
          .cost-breakdown-cards-mobile {
            display: none;
          }
        }

        .breakdown-card {
          border: 1px solid var(--color-border);
          border-radius: var(--border-radius-md);
          padding: 12px;
          background: var(--color-background);
        }

        .breakdown-card.acid {
          border-color: rgba(245, 158, 11, 0.35);
          background: rgba(245, 158, 11, 0.06);
        }

        .breakdown-card.micro {
          border-color: rgba(59, 130, 246, 0.35);
          background: rgba(59, 130, 246, 0.04);
        }

        .breakdown-card-header {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 8px;
        }

        .breakdown-card-name {
          font-weight: var(--font-semibold);
        }

        .breakdown-card-row {
          display: flex;
          justify-content: space-between;
          margin-top: 6px;
          font-size: var(--text-sm);
        }

        .breakdown-card-row.total {
          padding-top: 6px;
          border-top: 1px dashed var(--color-border);
          margin-top: 10px;
        }

        .cost-projection-section {
          padding: 0 var(--space-4) var(--space-4);
        }

        @media (min-width: 768px) {
          .cost-projection-section {
            padding: 0 var(--space-5) var(--space-5);
          }
        }

        .cost-projection-card {
          border: 1px solid var(--color-border);
          border-radius: var(--border-radius-md);
          padding: var(--space-4);
          background: var(--color-background);
        }

        .cost-projection-header {
          display: flex;
          align-items: center;
          gap: 10px;
          margin-bottom: 12px;
        }

        .cost-projection-stats {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 10px;
          margin-bottom: 12px;
        }

        .stat-label {
          display: block;
          color: var(--color-text-secondary);
          font-size: var(--text-xs);
        }

        .stat-value {
          display: block;
          font-weight: var(--font-semibold);
          margin-top: 2px;
        }

        .cost-projection-total {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 12px;
          border-radius: var(--border-radius-md);
          background: var(--color-background-secondary);
          margin-bottom: 10px;
        }

        .projection-label {
          display: block;
          color: var(--color-text-secondary);
          font-size: var(--text-xs);
        }

        .projection-value {
          display: block;
          font-weight: var(--font-bold);
          font-size: 1.1rem;
        }

        .cost-projection-note {
          display: flex;
          gap: 8px;
          color: var(--color-text-secondary);
          font-size: var(--text-sm);
        }

        .cost-unit-cards {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 10px;
          padding: 0 var(--space-4) var(--space-4);
        }

        @media (min-width: 768px) {
          .cost-unit-cards {
            padding: 0 var(--space-5) var(--space-5);
          }
        }

        .cost-unit-card {
          border: 1px solid var(--color-border);
          border-radius: var(--border-radius-md);
          padding: 12px;
          background: var(--color-background);
        }

        .cost-unit-label {
          display: block;
          color: var(--color-text-secondary);
          font-size: var(--text-xs);
        }

        .cost-unit-value {
          display: block;
          margin-top: 4px;
          font-weight: var(--font-bold);
        }

        .cost-summary-footer {
          padding: var(--space-4);
          border-top: 1px solid var(--color-border);
          color: var(--color-text-tertiary);
          font-size: var(--text-sm);
          text-align: center;
        }
      `}</style>
    </div>
  );
};

export default CostSummary;
