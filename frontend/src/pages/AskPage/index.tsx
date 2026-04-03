import { PageScaffold } from "../../components/PageScaffold";

export function AskPage() {
    return (
        <PageScaffold
            title="问答页占位"
            description="用于固定未来 ask 交互的页面结构。当前只保留问题输入区与答案展示区位置，不实现真实请求。"
            formTitle="问题输入区"
            resultTitle="答案与引用区"
        />
    );
}
