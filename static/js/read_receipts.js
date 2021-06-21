import $ from "jquery";
import SimpleBar from "simplebar";

import render_read_receipts from "../templates/read_receipts.hbs";
import render_read_receipts_modal from "../templates/read_receipts_modal.hbs";

import * as channel from "./channel";
import {$t} from "./i18n";
import * as loading from "./loading";
import * as overlays from "./overlays";
import * as people from "./people";

export function show_user_list(message_id) {
    $("body").append(render_read_receipts_modal());
    overlays.open_modal("read_receipts_modal", {
        autoremove: true,
        micromodal: true,
        on_show: () => {
            loading.make_indicator($("#read_receipts_modal .loading_indicator"));
            channel.get({
                url: `/json/messages/${message_id}/read_receipts`,
                idempotent: true,
                success(data) {
                    const users = data.user_ids.map((id) => people.get_by_user_id(id));
                    users.sort(people.compare_by_name);

                    loading.destroy_indicator($("#read_receipts_modal .loading_indicator"));
                    if (users.length === 0) {
                        $("#read_receipts_modal .read_receipts_info").text(
                            $t({defaultMessage: "No one has read this message yet."}),
                        );
                    } else {
                        $("#read_receipts_modal .modal__container").addClass(
                            "showing_read_receipts_list",
                        );
                        $("#read_receipts_modal .modal__content").append(
                            render_read_receipts({users}),
                        );
                        new SimpleBar($("#read_receipts_modal .modal__content")[0]);
                    }
                },
            });
        },
    });
}
