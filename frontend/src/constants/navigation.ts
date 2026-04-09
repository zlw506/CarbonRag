import type { UserRole } from "../types/auth";

export interface NavigationItem {
    path: string;
    label: string;
    roles: UserRole[];
}

const ALL_NAV_ITEMS: NavigationItem[] = [
    { path: "/", label: "Ask", roles: ["user", "admin"] },
    { path: "/carbon-calc", label: "Carbon Calc", roles: ["user", "admin"] },
    { path: "/report", label: "Reports", roles: ["user", "admin"] },
    { path: "/admin", label: "Admin", roles: ["admin"] },
];

export function getNavigationItems(role: UserRole) {
    return ALL_NAV_ITEMS.filter((item) => item.roles.includes(role));
}
