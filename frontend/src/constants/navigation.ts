import type { UserRole } from "../types/auth";

export interface NavigationItem {
    path: string;
    label: string;
    roles: UserRole[];
}

const ALL_NAV_ITEMS: NavigationItem[] = [
    { path: "/", label: "问答工作台", roles: ["user", "admin"] },
    { path: "/my-knowledge", label: "我的知识库", roles: ["user", "admin"] },
    { path: "/carbon-calc", label: "碳核算", roles: ["user", "admin"] },
    { path: "/report", label: "报告生成", roles: ["user", "admin"] },
];

export const ADMIN_NAV_ITEM: NavigationItem = {
    path: "/admin",
    label: "管理员入口",
    roles: ["admin"],
};

export function getNavigationItems(role: UserRole) {
    return ALL_NAV_ITEMS.filter((item) => item.roles.includes(role));
}
