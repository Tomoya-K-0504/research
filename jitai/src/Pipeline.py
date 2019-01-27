class Pipeline:
    """
    パイプラインが満たすべき条件を以下に示す
    - stepsによって処理を進める.
    - 最終ステップ(介入)以外の各stepで, EMAや実行時刻等に条件を適用し、条件を満たせばTrue, そうでなければFalseを返す

    """
    def __init__(self, steps):
        self.steps = steps

    def run(self):
        res = []
        for cond_name, event, suffix in self.steps[:-1]:
            if suffix == False:
                continue

            # dependが存在するとき
            if suffix:
                event.add_depend_class(suffix)

            res.append(event.run())

        return sum(res) == len(res)
